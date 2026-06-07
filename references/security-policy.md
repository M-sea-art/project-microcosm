# Security Policy

Default read-only. bootstrap, inspect, plan-change, simulate, and verify must not modify project source code.

Default exclusions: .env, private keys, access tokens, browser credentials, SSH directories, system key stores, node_modules, build caches, .git/objects, large binaries.

Do not execute untrusted code: no postinstall, setup.py, repository scripts, scanner binaries from the repo, or scenario eval.
