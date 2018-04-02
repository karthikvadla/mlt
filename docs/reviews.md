# Reviewer Checklist

"Next time" means never. So strive to do it the right way. Good reviews takes time.

 1) Do you understand it? You approve it, you own it. If there are bugs and the author is absent, you are responsible for the code and fixing it.
 Understandability comes over all other properties (code compaction, smart solutions, and so on); you cannot make code you don’t understand correct (purposefully), secure it, extend it, document it. Thus, make sure code can be understood locally.

 2) Is it correct? Once you understand the code, is it correct? Correct is a matter of fulfilling the promised behavior; make sure that there are no surprises for the user.

 3) Is it safe? No insecure code is worth it. We expose ourselves and our users by doing this and the hardest thing to get rid of, is a negative reputation.

 4) Is it legally compliant? Open Sourcing at Intel requires approval for all external components. Some Open Source licenses spread and will have implications on the outbound license for the project. Consult the dls-maintainers group before accepting new libraries, pulling in external code, Dockerfiles and the like.

 5) Is it robust? This is a key point of good design; is it hard to use the wrong way? Are there catastrophic consequences if used the wrong way?

 6) Is it simple? Simple code is crucial to secure, enhance, extend, explain and simple code is harder to write than complex. It takes time and effort to get to a simple solution; so is the PR as simple as it could be? This includes making sure the PR only does one thing.

 7) Is it tested? And have we tested the negative path beyond the happy path of “whether it works”. Does the tests allow changes to the implementation of APIs? In other words, strive for decoupling of the test and feature code.

 8) Is it documented? Undocumented features doesn’t exist to the user. Don’t expect anyone will read your code to understand how to use it. The PR description is a part of the documentation, describe what the problem is, how is it solved and how is it tested?

 9) Is the style consistent? Only when the above is checked of, then start worrying about code style. It wastes everyone’s time if you start nit picking before large problems (say, security concerns) are identified.

These are high level themes: for in depth guidance on what constitutes good versus bad (code smells), feel free to refer in the review to specific code smells from Code Code.
Make sure these are truly checked off before landing a PR.
