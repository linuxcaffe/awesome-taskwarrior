# CODE REVIEW NOTES
regarding stabilization of the codebase of the awesome-taskwarrior project

The goal here is to review core code components of the package-manager aspect of the project, to consolidate recent changes. Over it's development, ideas and models have evolved, and there is certainly cruft of old ideas that need to be streamlined to the current model. Things to look out for;

- previous ideas about a git-clone based distribution system, now the core components are all curl. That doen't mean git cloning is banned, or anything, I'm sure it may happen later. we should keep working clone_from_github code, inactive for now. be sure git cloning is not part of any core component.. for now.

- There was a directory model associated with the git clone concept, and it had a lot of simlinks. Programs no longer have subdirectories of ~/.task/hooks/ and simlinks (although there is no rule against users creating them) please refer to task-tree-final.txt in project files for the current model.

- IMPORTANT! seek out and change any reference to /home/djp/.task/, it should ALWAYS be seen as ~/.task/

- there have been times when python executables were referenced using the .py extension, ie tw.py, nn.py etc, and for use in command strings and having to simlink or alias the extension off of it is a pain. for peripheral programs like make-awesome-install.p it's fine, but tw, nn, etc will no longer be referred to with extension .py, so look out for hard-coding of such.

- Look out for ### NOTES ### I have left for you, here and there
 
- Migration between versions is "not a thing" at this stage. There is only 1 user (me) and he is very progress hungry and fault-tolerant! Omit any migration references or code.
