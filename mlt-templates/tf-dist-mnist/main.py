#
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: EPL-2.0
#


import json
import logging
import numpy as np
import os
import socket
import subprocess
import tensorflow as tf
import time

# You can turn on the gRPC messages by setting the environment variables below
# os.environ["GRPC_VERBOSITY"]="DEBUG"
# os.environ["GRPC_TRACE"] = "all"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # Get rid of the AVX, SSE

# Define parameters
FLAGS = tf.app.flags.FLAGS
tf.app.flags.DEFINE_float("learning_rate", 0.2, "Initial learning rate.")
tf.app.flags.DEFINE_integer("steps_to_validate", 10,
                            "Validate and print loss after this many steps")
tf.app.flags.DEFINE_integer("is_sync", 1, "Synchronous updates?")
tf.app.flags.DEFINE_string("train_dir", "/output", "directory to write "
                                                   "checkpoint files")
tf.app.flags.DEFINE_integer("num_epochs", 5, "number of epochs")
tf.app.flags.DEFINE_integer("batch_size", 1024, "batch size")


def create_done_queue(i, worker_list):
    """
    Queue used to signal termination of the i"th ps shard.
    Each worker sets their queue value to 1 when done.
    The parameter server op just checks for this.
    """

    with tf.device("/job:ps/task:{}".format(i)):
        return tf.FIFOQueue(
            len(worker_list), tf.int32, shared_name="done_queue{}".format(i))


def create_done_queues(ps_list, worker_list):
    return [create_done_queue(i, worker_list) for i in range(len(ps_list))]


def get_epoch(batch_size, x, y, num_classes):
    train_size = x.shape[0]
    image_width = x.shape[1]
    image_height = x.shape[2]
    image_channels = x.shape[3]

    epoch_length = train_size - train_size % batch_size
    batch_count = int(epoch_length / batch_size)

    # Shuffle and truncate arrays to equal 1 epoch
    zipped = list(zip(x, y))
    np.random.shuffle(zipped)
    data, labels = zip(*zipped)
    data = np.asarray(data)[:epoch_length]
    labels = np.asarray(labels)[:epoch_length]

    # Reshape arrays into batch_count batches of length batch_size
    data = data.reshape((batch_count, batch_size, image_width, image_height,
                         image_channels))
    labels = labels.reshape((batch_count, batch_size, num_classes))

    # Join batches of training examples with batches of labels
    epoch_of_batches = list(zip(data, labels))

    return epoch_of_batches


def main(_):
    start_time = time.time()

    logging.info("TensorFlow version: %s", tf.__version__)
    logging.info("TensorFlow git version: %s", tf.__git_version__)

    tf_config_json = os.environ.get("TF_CONFIG", "{}")
    tf_config = json.loads(tf_config_json)
    logging.info("tf_config: %s", tf_config)

    task = tf_config.get("task", {})
    task_index = task["index"]
    job_name = task["type"]
    logging.info("task: %s", task)

    cluster_spec = tf_config.get("cluster", {})
    logging.info("cluster_spec: %s", cluster_spec)
    worker_list = cluster_spec.get("worker", "{}")
    ps_list = cluster_spec.get("ps", "{}")

    logging.info("job_name: {}".format(job_name))
    logging.info("task_index: {}".format(task_index))

    # Hyperparameters
    learning_rate = FLAGS.learning_rate
    steps_to_validate = FLAGS.steps_to_validate

    num_inter_op_threads = 1
    num_intra_op_threads = 1

    config = tf.ConfigProto(
        inter_op_parallelism_threads=num_inter_op_threads,
        intra_op_parallelism_threads=num_intra_op_threads)

    run_options = tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE)
    run_metadata = tf.RunMetadata()  # For Tensorflow trace

    cluster = tf.train.ClusterSpec(cluster_spec)
    server = tf.train.Server(cluster, job_name=job_name, task_index=task_index)

    is_sync = (FLAGS.is_sync == 1)  # Synchronous or asynchronous updates
    is_chief = (task_index == 0)  # Am I the chief node (always task 0)

    if job_name == "ps":

        sess = tf.Session(server.target, config=config)
        queue = create_done_queue(task_index, worker_list)

        logging.info("\n")
        logging.info("*" * 30)
        logging.info("\nParameter server #{} on this machine.\n\nWaiting on "
                     "workers to finish.\n\nPress CTRL-\\ to terminate early."
                     .format(task_index))
        logging.info("*" * 30)

        # wait until all workers are done
        for i in range(len(worker_list)):
            sess.run(queue.dequeue())
            logging.info("Worker #{} reports job finished.".format(i))

        logging.info("Parameter server #{} is quitting".format(task_index))
        logging.info("Training complete.")

    elif job_name == "worker":

        if is_chief:
            logging.info("I am chief worker {} with task #{}".format(
                worker_list[task_index], task_index))
        else:
            logging.info("I am worker {} with task #{}".format(
                worker_list[task_index], task_index))

        with tf.device(
                tf.train.replica_device_setter(
                    worker_device="/job:worker/task:{}".format(task_index),
                    cluster=cluster)):
            global_step = tf.Variable(0, name="global_step", trainable=False)

            """
            BEGIN:  Data loader
            """
            # Load pre-shuffled MNIST data into train and test sets
            (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist. \
                load_data()

            x_train = np.expand_dims(x_train, -1)
            x_test = np.expand_dims(x_test, -1)

            x_train = x_train / 255.0  # Scale everything between 0 and 1
            x_test = x_test / 255.0  # Scale everything between 0 and 1
            num_classes = 10  # 10 classes for MNIST (0-9)

            # One-hot encode the labels so that we can perform categorical
            # cross-entropy loss
            y_train = tf.keras.utils.to_categorical(y_train, num_classes)
            y_test = tf.keras.utils.to_categorical(y_test, num_classes)

            epoch = get_epoch(FLAGS.batch_size, x_train, y_train, num_classes)
            num_batches = len(epoch)

            logging.info("Data loaded: {} batches of size {}".format(
                len(epoch), FLAGS.batch_size))

            """
            END:  Data loader
            """

            """
            BEGIN: Define our model
            """
            # Set keras learning phase to train
            tf.keras.backend.set_learning_phase(True)

            # Don't initialize variables on the fly
            tf.keras.backend.manual_variable_initialization(False)

            # this placeholder will contain our input digits
            img = tf.placeholder(tf.float32, shape=(None, x_train.shape[1],
                                                    x_train.shape[2], 1))

            inputs = tf.keras.layers.Input(tensor=img, name='Images')

            # Keras layers can be called on TensorFlow tensors:
            x = tf.keras.layers.Flatten()(inputs)
            layer_1 = tf.keras.layers.Dense(100, activation="linear")(x)
            preds = tf.keras.layers.Dense(10, activation="softmax")(
                layer_1)  # output layer with 10 units and a softmax activation

            model = tf.keras.models.Model(inputs=[inputs], outputs=[preds])

            label = tf.placeholder(tf.float32, shape=(None, 10))

            loss_value = tf.reduce_mean(
                tf.keras.backend.categorical_crossentropy(label, preds))

            values, indices = tf.nn.top_k(preds, 10)
            table = tf.contrib.lookup.index_to_string_table_from_tensor(
                tf.constant([str(i) for i in range(10)]))
            prediction_classes = table.lookup(tf.to_int64(indices))

            with tf.name_scope('accuracy'):
                with tf.name_scope('correct_prediction'):
                    correct_prediction = tf.equal(tf.argmax(preds, 1),
                                                  tf.argmax(label, 1))
                with tf.name_scope('accuracy'):
                    accuracy = tf.reduce_mean(tf.cast(correct_prediction,
                                                      tf.float32))

            logging.info("Model defined:")
            logging.info(model.summary())

            """
            END: Define our model
            """

            # Define gradient descent optimizer
            optimizer = tf.train.GradientDescentOptimizer(learning_rate)

            grads_and_vars = optimizer.compute_gradients(
                loss_value, model.trainable_weights)

            if is_sync:
                rep_op = tf.train.SyncReplicasOptimizer(
                    optimizer,
                    replicas_to_aggregate=len(worker_list),
                    total_num_replicas=len(worker_list),
                    use_locking=True)

                train_op = rep_op.apply_gradients(
                    grads_and_vars, global_step=global_step)

                init_token_op = rep_op.get_init_tokens_op()

                chief_queue_runner = rep_op.get_chief_queue_runner()

            else:
                train_op = optimizer.apply_gradients(
                    grads_and_vars, global_step=global_step)

            init_op = tf.global_variables_initializer()

            saver = tf.train.Saver()

            # These are the values we wish to print to TensorBoard
            tf.summary.scalar("loss", loss_value)
            tf.summary.histogram("loss", loss_value)
            tf.summary.histogram("loss", loss_value)
            tf.summary.scalar("accuracy", accuracy)
            tf.summary.histogram("accuracy", accuracy)
            tf.summary.histogram("accuracy", accuracy)
            tf.summary.image("mnist_images", img, max_outputs=5)

        # Send a signal to the ps when done by simply updating a queue in
        # the shared graph
        enq_ops = []
        for q in create_done_queues(ps_list, worker_list):
            qop = q.enqueue(1)
            enq_ops.append(qop)

        # Only the chief does the summary
        if is_chief:
            summary_op = tf.summary.merge_all()
        else:
            summary_op = None

        # TODO:  Theoretically I can pass the summary_op into
        # the Supervisor and have it handle the TensorBoard
        # log entries. However, doing so seems to hang the code.
        # For now, I just handle the summary calls explicitly.
        sv = tf.train.Supervisor(
            is_chief=is_chief,
            logdir=os.path.join(FLAGS.train_dir, "run" +
                                time.strftime("_%Y%m%d_%H%M%S")),
            init_op=init_op,
            summary_op=None,
            saver=saver,
            global_step=global_step,
            save_model_secs=20
        )  # Save the model (with weights) every 60 seconds

        # TODO:
        # I'd like to use managed_session for this as it is more abstract
        # and probably less sensitive to changes from the TF team. However,
        # I am finding that the chief worker hangs on exit if I use
        # managed_session.
        with sv.prepare_or_wait_for_session(
                server.target, config=config) as sess:
            # with sv.managed_session(server.target) as sess:
            if is_chief and is_sync:
                sv.start_queue_runners(sess, [chief_queue_runner])
                sess.run(init_token_op)
            step = 0

            # Start TensorBoard on the chief worker
            if is_chief:
                cmd = 'tensorboard --logdir={}'.format(FLAGS.train_dir)
                tensorboard_pid = subprocess.Popen(cmd,
                                                   stdout=subprocess.PIPE,
                                                   shell=True,
                                                   preexec_fn=os.setsid)
                chief_ip = socket.gethostbyname(socket.gethostname())
                logging.info("Chief node started TensorBoard http://{}:6006".
                             format(chief_ip))

                # Go for a few epochs of training
            NUM_STEPS = FLAGS.num_epochs * num_batches
            while (not sv.should_stop()) and (step < NUM_STEPS):
                batch_idx = step % num_batches  # Which batch?

                data = epoch[batch_idx][0]
                labels = epoch[batch_idx][1]

                # For n workers, break up the batch into n sections
                # Send each worker a different section of the batch
                data_range = int(FLAGS.batch_size / len(worker_list))
                start = data_range * task_index
                end = start + data_range

                history, loss_v, acc_val, step = sess.run(
                    [train_op, loss_value, accuracy, global_step],
                    feed_dict={
                        img: data[start:end],
                        label: labels[start:end]
                    })

                if step % steps_to_validate == 0:
                    if is_chief:
                        summary = sess.run(
                            summary_op,
                            feed_dict={
                                img: data[start:end],
                                label: labels[start:end]
                            })

                        sv.summary_computed(sess,
                                            summary)  # Update the summary

                    logging.info("[step: {:,} of {:,}]  loss: {:.4f}, "
                                 "accuracy: {:.2f}".format(step, NUM_STEPS,
                                                           loss_v, acc_val))

                # Shuffle every epoch
                if (batch_idx == 0) and (step > num_batches):
                    logging.info("Shuffling epoch")
                    epoch = get_epoch(FLAGS.batch_size, x_train, y_train,
                                      num_classes)

            # Send a signal to the ps when done by simply updating a queue in
            # the shared graph
            for op in enq_ops:
                sess.run(
                    op
                )  # Send the "work completed" signal to the parameter server

        logging.info("Finished work on this node.")

        sv.request_stop()

    logging.info("Finished in {} seconds".format(time.time() - start_time))


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    tf.app.run()
