"""Harbor's OpenCode agent with one install fallback for Debian 11 images.

Before installing OpenCode, Harbor installs `curl bash nodejs npm` with the image's package manager. Two tasks,
`qemu-startup` and `qemu-alpine-ssh`, use Debian 11 (bullseye) images whose sources point at
`deb.debian.org/debian-security`. Since bullseye's end of life that mirror's index still lists packages its pool
no longer serves (404), so the install fails and the agent never starts. No other task in the dataset uses
bullseye.

When the stock install fails and the image has that source, this points the security source at
`archive.debian.org` (which still serves those packages) and retries the same install once. Every image where the
stock install works gets exactly the stock install. The agent, its prompt and its OpenCode configuration are
unchanged. The changed source stays in the container, so `apt-get` also works for the model there, as it did
when the task was made.
"""

from harbor.agents.installed.opencode import OpenCode

SECURITY_TO_ARCHIVE = (
    "grep -qs 'deb.debian.org/debian-security' /etc/apt/sources.list && "
    "sed -i 's|deb.debian.org/debian-security|archive.debian.org/debian-security|' /etc/apt/sources.list"
)


class OpenCodeAptFallback(OpenCode):
    async def ensure_system_dependencies(self, environment, dependencies):
        try:
            await super().ensure_system_dependencies(environment, dependencies)
        except Exception as stock_failure:
            try:
                await self.exec_as_root(environment, command=SECURITY_TO_ARCHIVE)
            except Exception:
                raise stock_failure  # not a bullseye-security image: keep the stock failure
            self.logger.warning("system install failed; retrying with debian-security from archive.debian.org")
            await super().ensure_system_dependencies(environment, dependencies)
