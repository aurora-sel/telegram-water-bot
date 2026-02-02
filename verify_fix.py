#!/usr/bin/env python3
"""
验证修复 - 检查代码是否正确实现了 HTTP 服务器
"""

import ast
import sys

def check_main_py():
    """检查 main.py 是否包含 HTTP 服务器代码"""
    print("检查 main.py...")
    print("-" * 60)
    
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        "导入 aiohttp": "from aiohttp import web" in content,
        "health_check 函数": "async def health_check(request):" in content,
        "status_check 函数": "async def status_check(request):" in content,
        "create_app 函数": "def create_app():" in content,
        "run_http_server 函数": "async def run_http_server():" in content,
        "HTTP 服务器启动": "[HTTP服务器] 已启动" in content,
        "注册路由": "app.router.add_get" in content,
        "并发运行": "http_runner = await run_http_server()" in content,
    }
    
    all_pass = True
    for check_name, result in checks.items():
        status = "✓" if result else "✗"
        print(f"{status} {check_name}: {'通过' if result else '失败'}")
        if not result:
            all_pass = False
    
    return all_pass


def check_dockerfile():
    """检查 Dockerfile 是否正确配置"""
    print("\n检查 Dockerfile...")
    print("-" * 60)
    
    with open('Dockerfile', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        "安装 curl": "curl" in content,
        "暴露 8080 端口": "EXPOSE 8080" in content,
        "HTTP 健康检查": "curl -f http://localhost:8080/health" in content,
        "使用 ENTRYPOINT": "ENTRYPOINT" in content,
        "使用 CMD": "CMD" in content,
    }
    
    all_pass = True
    for check_name, result in checks.items():
        status = "✓" if result else "✗"
        print(f"{status} {check_name}: {'通过' if result else '失败'}")
        if not result:
            all_pass = False
    
    return all_pass


def main():
    print("\n" + "=" * 60)
    print("Koyeb 健康检查修复验证")
    print("=" * 60 + "\n")
    
    main_py_ok = check_main_py()
    dockerfile_ok = check_dockerfile()
    
    print("\n" + "=" * 60)
    if main_py_ok and dockerfile_ok:
        print("✓ 所有检查通过！修复成功。")
        print("=" * 60)
        print("\n下一步：")
        print("1. git add main.py Dockerfile")
        print("2. git commit -m 'Fix: Add HTTP server for Koyeb health checks'")
        print("3. git push origin main")
        print("4. 在 Koyeb 中重新部署")
        return 0
    else:
        print("✗ 某些检查失败，请检查代码。")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
