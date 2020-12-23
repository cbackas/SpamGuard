# SpamGuard

Microsoft's spam filter became uselsss about a yaer ago. Their email rules aren't powerful enough to make the spam stop. So  here I am.

Uses [mailsuite](https://github.com/cbackas/mailsuite) (well my fork with a couple fixes) which handles the imap/idle heavy lifting

##### Runs in Docker (of course)
> docker run -d -e 'IMAP_HOST'='' -e 'IMAP_PORT'='993' -e 'AUTH_USERNAME'='' -e 'AUTH_PASSWORD'='' cbackas/spamguard:latest