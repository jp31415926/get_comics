import asyncio
from playwright.async_api import async_playwright
import requests
from datetime import date
import paramiko
import os


def sftp_transfer_via_agent(hostname, port, username, local_file, remote_path):
    """
    Transfers a file to a remote server using SFTP with SSH keys from ssh-agent.

    :param hostname: Remote server address (e.g., 'example.com')
    :param port: SSH port (usually 22)
    :param username: SSH username
    :param local_file: Path to the local file to be uploaded
    :param remote_path: Path on the remote server to upload the file to
    """
    print(f"Attempting to transfer '{local_file}' to '{username}@{hostname}:{remote_path}'")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Use ssh-agent to get available keys
    agent = paramiko.Agent()
    agent_keys = agent.get_keys()
    sftp = None

    try:
        if not agent_keys:
            print("No SSH keys found in the ssh-agent.")
            raise RuntimeError("No SSH keys found in the ssh-agent.")

        # Attempt to connect with each key until successful
        for key in agent_keys:
            try:
                ssh.connect(hostname=hostname, port=port, username=username, pkey=key)
                print(f"SSH Connected with key {key.comment}.")
                break
            except paramiko.AuthenticationException:
                continue
        else:
            print("Authentication failed using ssh-agent keys.")
            raise RuntimeError("Authentication failed using ssh-agent keys.")

        # Perform SFTP transfer
        sftp = ssh.open_sftp()
        # fl = sftp.listdir(remote_path)
        # for fn in fl:
        #     print(fn)


        sftp.put(local_file, remote_path)

        #print(f"File '{local_file}' transferred to '{username}@{hostname}:{remote_path}'")

    except Exception as e:
        print(f"Error: {e}")

    # Clean up
    if sftp: sftp.close()
    ssh.close()


async def stealth(page):
    """Inject advanced stealth scripts to avoid detection."""
    await page.add_init_script("""
        // Pass the Webdriver check
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

        // Fake plugins
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});

        // Fake languages
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});

        // Fake Chrome runtime
        window.chrome = {runtime: {}, loadTimes: () => ({})};

        // Fake Permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({state: Notification.permission}) :
                originalQuery(parameters)
        );

        // Fake userAgentData (modern Chrome)
        Object.defineProperty(navigator, 'userAgentData', {
            get: () => ({
                brands: [
                    {brand: "Google Chrome", version: "116"},
                    {brand: "Chromium", version: "116"},
                    {brand: ";Not A Brand", version: "99"}
                ],
                mobile: false,
                platform: "Windows"
            })
        });

        // Fake WebGL vendor & renderer
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) { return "Intel Inc."; }
            if (parameter === 37446) { return "Intel Iris OpenGL Engine"; }
            return getParameter(parameter);
        };
    """)

async def download_comic(url: str, selector: str, filename_prefix: str, filename_suffix: str = "gif"):
    """
    Download a comic image from a given URL using Playwright.

    Args:
        url (str): The web page URL containing the comic.
        selector (str): CSS selector for the comic image.
        filename_prefix (str): Prefix for the saved filename.
        filename_suffix (str): Suffix for the saved filename.

    Returns:
        str: Path to saved image file, or None if not found.
    """

    filename = f"{filename_prefix}-{date.today().strftime('%Y%m%d')}.{filename_suffix}"

    if os.path.isfile(filename):
        return filename

    try:
        async with async_playwright() as p:
            
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=100,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process"
                ]
            )
            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/116.0.0.0 Safari/537.36"
            )

            context = await browser.new_context(
                viewport={"width": 1400, "height": 900},
                user_agent=user_agent,
                locale="en-US"
            )

            page = await context.new_page()

            await stealth(page)

            print(f"Navigating to {url} ...")
            try:
                await page.goto(url, wait_until="load", timeout=10000)
                await asyncio.sleep(2)  # extra time for JS
                print("Page loaded.")
            except Exception as e:
                print(f"Timeout waiting for page to load. Trying to get comic anyway...")

            print("Title:", await page.title())
            print("Current URL:", page.url)

            try:
                await page.wait_for_selector(selector, timeout=10000)

            except Exception as e:
                raise RuntimeError(f"Selector '{selector}' not found") from e

            img_element = await page.query_selector(selector)
            img_url = await img_element.get_attribute("src")

            if not img_url:
                raise RuntimeError("No image URL found.")

            r = requests.get(img_url)
            r.raise_for_status()
            with open(filename, "wb") as f:
                f.write(r.content)

            print(f"Downloaded comic: {filename}")
            await browser.close()
            return filename

    except Exception as e:
        print(f"Error: {e}")

        await page.screenshot(path=f"{filename_prefix}_debug.png")
        print(f"Saved debug screenshot: {filename_prefix}_debug.png")

        print("Debug mode: taking snapshot and HTML dump...")
        await page.screenshot(path=f"{filename_prefix}_error_debug.png")
        html = await page.content()
        with open(f"{filename_prefix}_error_debug.html", "w", encoding="utf-8") as f:
            f.write(html)

        return None


if __name__ == "__main__":
    fn = list()
    # Loose Parts
    fn.append(asyncio.run(download_comic(u"https://www.gocomics.com/looseparts", 'img[class*="Comic_comic__image"]', "lp", "gif")))
    # Calvin and Hobbes
    fn.append(asyncio.run(download_comic(u"https://www.gocomics.com/calvinandhobbes", 'img[class*="Comic_comic__image"]', "ch", "gif")))
    # Off the Mark
    fn.append(asyncio.run(download_comic(u"https://www.gocomics.com/offthemark", 'img[class*="Comic_comic__image"]', "otm", "gif")))
    # F Minus
    fn.append(asyncio.run(download_comic(u"https://www.gocomics.com/fminus", 'img[class*="Comic_comic__image"]', "fm", "gif")))
    # Daddy's Home
    fn.append(asyncio.run(download_comic(u"https://www.gocomics.com/daddyshome", 'img[class*="Comic_comic__image"]', "dh", "gif")))

    #fn.append("lp-20251007.gif")

    for f in fn:
        sftp_transfer_via_agent("attila.gcfl.net", 9876, "jp", f, f"/home/jp/tmp/{f}")
