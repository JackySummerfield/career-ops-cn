# JD Fetching Strategy

Use this reference whenever the user provides a job-posting URL.

## Goal

Extract the rendered job description with enough evidence to identify the company, role, location, responsibilities, requirements, and compensation when shown. Preserve the source URL. Do not collect cookies, tokens, local storage, passwords, or unrelated account data.

## Retrieval ladder

1. **Direct semantic read** — Use an available web/HTTP/connector tool. Accept the result only if it contains the role plus substantive responsibilities and requirements.
2. **Search-assisted recovery** — Search the exact URL, job ID, page title, or `site:<domain>` when the direct response is a shell, login wall, or JavaScript placeholder. Prefer the employer's canonical posting over reposts.
3. **Rendered browser DOM** — In Codex, discover and follow the available Browser or Chrome control skill. Open the URL, wait for rendering, dismiss ordinary overlays when safe, expand collapsed job-detail sections, and read the visible page text. Reuse an existing signed-in browser only through supported browser controls.
4. **User-assisted browser step** — If login, consent, or CAPTCHA blocks the page, ask the user to complete that step in the selected browser, then continue reading the rendered DOM. Never attempt to bypass a CAPTCHA or extract session secrets.
5. **Screenshot fallback** — Ask for screenshots of the job title/header, responsibilities, and requirements. Read them directly with vision; do not make the user run OCR. Prefer 2–4 tightly cropped screenshots with slight vertical overlap over many full-screen captures. Transcribe uncertain words conservatively and mark any visibly clipped section.
6. **Manual text fallback** — Ask the user to paste the JD only when screenshots are unavailable or illegible. State the observed blocker rather than saying all SPA pages are unsupported.

## Completeness check

Before evaluation, verify that the extracted content includes:

- company and role;
- location or work arrangement when present;
- at least one substantive responsibilities section;
- at least one qualifications/requirements section;
- salary, benefits, language, and application deadline when present.

If navigation, recommendations, or company boilerplate dominate the text, isolate the job-detail container or ask the user to confirm the extracted JD before scoring.

## Platform notes

- Treat SPA rendering and anti-automation as runtime observations, not permanent platform facts.
- Boss Zhipin may show a title/URL in a normal signed-in tab but return an empty DOM or blank viewport after supported browser control attaches. Direct HTTP and mobile-host requests may redirect to a JavaScript security challenge instead of returning the JD.
- Search engines may expose a title and partial cached snippets for a specific Boss job URL, but snippets are not complete enough for scoring unless responsibilities and requirements are both recovered.
- Do not integrate tools that require copying session cookies, defeating the security challenge, disabling robots compliance, or using unofficial private endpoints. Boss's published user agreement prohibits unapproved third-party access, scraping, and circumvention. For this site, stop after low-frequency read-only attempts and use screenshots.
- Workday and other ATS pages often require expanding sections or following a canonical job-detail link before the complete text appears.
- Use `util/fetch_jd.py` only when the client lacks supported browser control. It is a fallback, not the Codex default.
