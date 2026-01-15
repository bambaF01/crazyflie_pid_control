This file decribes the basics to understand the CI pulling updates from bitcraze'
repository

images are downloaded from docker hub but as often used, the unbuntu one is cached
in inria and takes a lot less time to pull than bitcarze's released image -- here
we have very few dependancies so it's ok.



===== PIPELINE DESCRIPTION =====

you might take a look at https://docs.gitlab.com/ee/ci/yaml/ for keywords reference
First the jobs makes installs and setups local config to be able to push if needed
The git fetch origin is necessary because of gitlab's default fetch-only repositor
policy.
Then, we fetch bitcraze's latest release on master, try to merge it, clone and
install the inria cflib, install the client then check for installations

[Failure] if cannot merge automatically, git merge returns non-zero
[Failure] if pip3 cannot find the setup.py, returns non-zero
[Failure] if cflib not installs, 'which' doesn't print and returns non-zero
[Failure] on push -> check that the url and access token are correctly set-up



===== PROJECT ACCESS TOKENS =====

The repo relies on project access tokens to push it's automatic updates fetched
from bitcraze repository. Those have expiration dates of 1 year you will
eventually need to regenerate one.

To push a new project access token,
  >Settings>Access Token>Add new Token
     - give the token at least dev role and write repository access and as few
     rights as needed
     - save the string and create a variable in >Settings>CI/CD>Variables with
     the name "CI_PROJECT_TOKEN", the token string as value and better with
     [masked] attribute



===== SCHEDULING =====

>Build>Pipeline schedules
as they change the branch history, better have pipeline schedules when noone is
working eg. 4am



===== OPTIMISATIONS ======

As this pipeline is meant to be run once a month or once a week AT MOST, few
optimisations has been made in order to push for clarity and robustness



===== IMPROVEMENTS =====

-> watch out for gitlab updates, as project deploy token that can be made with indefinite duration MIGHT have pushing rights on repositories.
