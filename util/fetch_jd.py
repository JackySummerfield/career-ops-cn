"""Fetch a rendered SPA job description with Playwright as a local fallback.

Use this script only when the client has no supported browser-control capability.
If a login, CAPTCHA, or security challenge appears, complete ordinary user steps
manually or stop and use screenshots. This script does not bypass anti-automation
controls or read browser session secrets.
"""

import argparse
import sys
import time
from pathlib import Path

def fetch_jd(url: str, output_dir: str = "jds", channel: str | None = None) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit(
            "Playwright is not installed. Install it only if your client has no supported "
            "browser-control skill: pip install playwright && playwright install chromium"
        ) from exc

    with sync_playwright() as p:
        launch_options = {
            "headless": False,
        }
        if channel:
            launch_options["channel"] = channel
        browser = p.chromium.launch(**launch_options)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        print(f"正在打开: {url}")
        page.goto(url, wait_until="domcontentloaded")

        # 等待页面内容加载，给JS渲染一点时间
        time.sleep(3)

        # 检查页面是否正常加载（简单判断：页面文本长度）
        body_text = page.inner_text("body")
        if len(body_text.strip()) < 200:
            print("\n⚠️  页面内容过少，可能遇到验证码或登录拦截")
            print("    请在浏览器中完成操作，然后回到终端按 Enter 继续...")
            input()
            time.sleep(2)
            body_text = page.inner_text("body")

        # 再次确认：让用户决定是否内容已加载完整
        print("\n页面已加载，请确认浏览器中职位详情已完整显示。")
        print("按 Enter 提取内容（如需等待加载，请先在浏览器中操作完毕）...")
        input()

        # 提取页面文本
        body_text = page.inner_text("body")

        # 获取页面标题
        title = page.title()

        browser.close()

    # 组装结果
    result = f"# {title}\n\nURL: {url}\n\n---\n\n{body_text}"

    # 保存到文件
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # 用时间戳+简化URL作为文件名
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"jd_{timestamp}.txt"
    filepath = output_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"\n✅ 已保存到: {filepath}")
    print(f"   文本长度: {len(body_text)} 字符")

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch a rendered job description page")
    parser.add_argument("url", nargs="?", help="job posting URL")
    parser.add_argument("--output-dir", default="jds", help="directory for extracted text")
    parser.add_argument(
        "--channel",
        choices=("chrome", "msedge"),
        help="use an installed browser channel; omit to use Playwright Chromium",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    url = args.url or input("请输入职位URL: ").strip()

    if not url:
        print("❌ 未提供URL")
        sys.exit(1)

    content = fetch_jd(url, output_dir=args.output_dir, channel=args.channel)

    # 打印前500字符预览
    print("\n" + "=" * 60)
    print("预览（前500字符）:")
    print("=" * 60)
    print(content[:500])
    if len(content) > 500:
        print(f"\n... (共 {len(content)} 字符，完整内容已保存到文件)")
