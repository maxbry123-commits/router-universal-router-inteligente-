---
source_url: https://docs.x.ai/grok-bot/get-started
fetched: 2026-10-25
tool: firecrawl_scrape (markdown)
---

# Get started

Set up Grok Bot, create your first Bot, and hand it a useful task.

## Before you begin

You need:

- An eligible plan: every paid individual Cursor plan or the Cursor Teams plan, an individual SuperGrok, SuperGrok Plus, or SuperGrok Heavy subscription linked to your Cursor account, or a seat on a self-serve Grok Business plan (see [Plans and billing](https://cursor.com/help/grok-bot/plans))
- The Grok Bot desktop app for macOS, Windows, or Linux
- An app or website where your first Bot can do useful work

You can also [set up and use Grok Bot on mobile](https://docs.x.ai/grok-bot/mobile).

> Grok Bot requires cloud data storage. Accounts using Legacy Privacy Mode must move to a supported Cursor data setting before Grok Bot can start. Open [Cursor privacy settings](https://cursor.com/dashboard/settings?openPrivacy=true) to review the account setting.

## 1. Install the desktop app

Open the [Grok Bot downloads page](https://x.ai/bot) and choose the download for your computer.

### macOS

1. Choose the Apple silicon or Intel download.
2. Open the downloaded disk image.
3. Drag **Grok Bot** to **Applications**.
4. Open Grok Bot. If macOS asks for confirmation, choose **Open**.

To check which download you need, open **Apple menu -> About This Mac**. A **Chip** field means Apple silicon; a **Processor** field means Intel.

### Windows

1. Choose the x64 or Arm64 download.
2. Run the installer.
3. Open Grok Bot from the Start menu.

To check the architecture, open **Settings -> System -> About -> System type**.

### Linux

Linux builds publish with every stable release. Get them under **More downloads** on [x.ai/bot](https://x.ai/bot).

1. Choose the x64 or Arm64 download in the format your distribution uses: a `.deb` package for Debian and Ubuntu, an `.rpm` package for Fedora and RHEL, or an AppImage for other distributions.
2. Install the `.deb` or `.rpm` with your package manager, or make the AppImage executable and run it.
3. Open Grok Bot from your application launcher.

To check the architecture, run `uname -m` in a terminal: `x86_64` means x64 and `aarch64` means Arm64.

Grok Bot checks for updates automatically. You can also use **Check for Updates** from **Settings -> Updates**.

## 2. Sign in

1. Choose **Sign in** on the welcome screen. If you are already in the app, use **Sign In with Cursor** from Settings.
2. Finish authentication in the browser window that opens.
3. Return to Grok Bot after the browser confirms the sign-in.
4. If your access comes from a SuperGrok subscription, link it when the app asks. On iPhone and Android, the access screen offers **Link Grok Account** and then **Finished Linking? Refresh My Status**; on desktop, **Settings -> Usage & Billing** offers **Get Access with Grok**.

Grok Bot uses your Cursor account. If your organization requires single sign-on (SSO), complete the normal organization sign-in flow.

On first use, click through a short intro. Computer setup runs in the background, and Grok Bot sets up your first Bot, named **Grok Bot**, and opens a chat with it.

## 3. Create your first Bot

Give each Bot one primary job in its first message and ask it to remember how it should work. To rename it, click its name at the top of the chat to open its details. For example:

> Your job is product performance. Investigate product-performance questions with our observability tools. Preserve links and screenshots, separate evidence from hypotheses, and lead with the highest-impact issue. Never change production settings. Remember this for future work.

Focused Bots build more useful context than one catch-all Bot. You can add more Bots later with **New -> Create new Bot** when work naturally splits into distinct roles. On a Cursor team, open the command palette and choose **Create new Team Bot** to make a Bot your teammates can chat with; see [Team Bots](https://docs.x.ai/grok-bot/team-bots).

## 4. Give it a first task

Type in the composer, or dictate with **Start voice input** (`Cmd/Ctrl+D` on desktop; **Start dictation** on iPhone and Android). You can also choose **Start voice chat** for a live conversation.

A strong request includes:

1. **Outcome:** What should be finished?
2. **Sources:** Which apps, websites, files, or conversations matter?
3. **Constraints:** What must the Bot avoid or ask before doing?
4. **Deliverable:** What should it return?
5. **Review point:** When should it stop for you?

For a five-minute first result that needs no connector or website login, attach a document and try:

> Summarize this document in five bullets. List every date, decision, and open question in a separate section. Cite the page or section for each item. Do not change the source file.

Then try a task in one of your tools:

> Open our analytics dashboard and compare new-user activation for this week with the previous four weeks. Identify the largest step-level change and draft a short investigation plan with links to the relevant charts. Do not change any dashboards. Ask me to sign in if needed.

Before allowing external changes, review [Approvals, security, and privacy](https://docs.x.ai/grok-bot/approvals-security-and-privacy).

## 5. Sign in to the tools it needs

When the Bot reaches an app that requires authentication, it may ask you to take over the computer.

1. Choose **Take over** on the request in the conversation.
2. Enter the password, passkey, two-factor code, or complete the CAPTCHA yourself.
3. Choose **I'm done** to hand control back.

The Bot doesn't see your password. The browser session persists on your shared Grok Bot computer, so other Bots can use the same signed-in session when appropriate.

For supported services, you can also install a plugin from **Connect apps** in the sidebar and authenticate it in your browser.

## 6. Review the result

Ask the Bot to revise anything that is incomplete or formatted incorrectly. Name the lasting preference explicitly:

> Use this format for future weekly reports: five bullets, source links inline, and a final section called "Decisions needed."

When the process is stable, ask the Bot to save it as a skill or [create a routine](https://docs.x.ai/grok-bot/skills-routines-and-automations).

## If something doesn't work

Most setup problems clear after you fully quit and reopen the app. For symptom-by-symptom help with the computer, routines, plugins, and sign-in, see [Troubleshooting](https://docs.x.ai/grok-bot/troubleshooting), or [contact support](https://docs.x.ai/grok-bot/troubleshooting#before-contacting-support).

## Next steps

- [Create and manage more Bots](https://docs.x.ai/grok-bot/bots)
- [Use apps and the cloud computer](https://docs.x.ai/grok-bot/computer-and-apps)
- [Attach files and review results](https://docs.x.ai/grok-bot/files-and-results)
- [Set approval and privacy controls](https://docs.x.ai/grok-bot/approvals-security-and-privacy)

Last updated (por la fuente): October 22, 2026
