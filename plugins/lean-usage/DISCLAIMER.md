# Experimental AI software: risk notice and disclaimer

**THIS IS EXPERIMENTAL, EARLY-ALPHA AI SOFTWARE. USE IT AT YOUR OWN RISK.**

The software, skills, hooks, scripts, documentation, examples, reports, and related
outputs may contain AI-generated or AI-assisted material. They may be incomplete,
incorrect, insecure, misleading, incompatible with your environment, or unsuitable
for your intended use. Tests, reviews, successful builds, and published examples
do not guarantee correctness, safety, mathematical validity, or future behavior.

## Automatic execution and operational risks

Claude Code activates the installed plugin's hooks automatically when the plugin
is enabled, without a separate per-hook approval step. Codex applies its own hook
trust and enablement controls. Hook execution can run commands and change local
files. SessionStart may create or replace a managed wrapper symlink; build workflows
can download dependencies, write artifacts and logs, and consume substantial CPU,
memory, disk space, time, or metered services.

Possible consequences include lost, overwritten, corrupted, or exposed data;
incorrect proofs or research conclusions; misleading verification claims; service
interruption; security incidents; unexpected costs; and damage to other software
or workflows. Guard hooks are heuristic workflow aids, not security boundaries.
The wrapper does not provide hard CPU or memory isolation. AI agents may disregard
instructions or act outside the intended workflow.

Review the code and permissions before enabling it. Use isolated environments,
least privilege, recoverable backups, and independent verification appropriate to
the consequences of failure. Avoid exposing credentials or sensitive data. Do not
rely on this software as the sole basis for publication, deployment, or a consequential
decision. It has not been validated for safety-critical use. These are safety
recommendations, not additional restrictions on rights granted by the license.

## No warranty

TO THE FULLEST EXTENT PERMITTED BY APPLICABLE LAW, AND EXCEPT AS EXPRESSLY AGREED
IN WRITING BY THE RELEVANT PARTY, THE MATERIALS ARE PROVIDED "AS IS" AND "AS
AVAILABLE," WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EXPRESS, IMPLIED, OR
STATUTORY, INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE,
NON-INFRINGEMENT, ACCURACY, SECURITY, RELIABILITY, OR ERROR-FREE OR UNINTERRUPTED
OPERATION. NO SUPPORT, MAINTENANCE, CORRECTION, OR CONTINUED AVAILABILITY IS PROMISED.
YOU BEAR THE RISK OF USE AND THE COST OF NECESSARY RECOVERY, REPAIR, AND VERIFICATION.

## Limitation of liability

TO THE FULLEST EXTENT PERMITTED BY APPLICABLE LAW, AND EXCEPT AS EXPRESSLY AGREED
IN WRITING BY THE RELEVANT PARTY, NO COPYRIGHT HOLDER, AUTHOR, CONTRIBUTOR,
MAINTAINER, OR DISTRIBUTOR SHALL BE LIABLE FOR ANY CLAIM, LOSS, OR DAMAGE ARISING
FROM OR RELATED TO THE MATERIALS OR THEIR USE OR INABILITY TO BE USED, WHETHER
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY, OR PUNITIVE,
INCLUDING LOSS OF DATA, PROFITS, RESEARCH WORK, GOODWILL, OR BUSINESS OPPORTUNITY,
BUSINESS INTERRUPTION, OR PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES, UNDER
CONTRACT, TORT, OR ANY OTHER THEORY OF LIABILITY, EVEN IF ADVISED OF THE POSSIBILITY
OF SUCH DAMAGE.

## License and legal limits

The project remains licensed under GPL-3.0-or-later. See the
[repository license](https://github.com/mysticflounder/lean-usage/blob/main/LICENSE),
especially GPLv3 sections 15–17. This notice explains risks and emphasizes the
applicable warranty and liability limitations; it does not replace the license,
impose an indemnity, or add restrictions on copying, modification, or distribution.
If this notice conflicts with the applicable license, the license controls.

Nothing here excludes liability or rights that applicable law does not allow to
be excluded, or overrides a binding written warranty or liability undertaking by
the relevant party. The legal effect of any disclaimer depends on the applicable
law and circumstances; this notice is not a guarantee of immunity from liability.
