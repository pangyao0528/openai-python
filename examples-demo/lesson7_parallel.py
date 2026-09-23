"""
Lesson 7: 并行工具调用 (Parallel Tool Calling) —— 使用 asyncio.gather 榨干网络性能
"""
import asyncio
import time
import json

# 模拟一个有网络延迟的远程微服务调用（例如请求第三方气象服务或数据库）
async def mock_remote_api(city: str) -> str:
    print(f"   ⏳ [协程启动] 开始请求 {city} 的气象微服务 (模拟耗时 1.5 秒)...")
    await asyncio.sleep(1.5) # 模拟 1.5 秒网络 I/O 延迟
    print(f"   ✅ [协程完成] 成功获取 {city} 的气象数据！")
    return json.dumps({"city": city, "temp": 25, "status": "晴朗"}, ensure_ascii=False)

async def test_parallel_vs_serial():
    cities = ["北京", "上海", "广州", "深圳", "成都"]
    print("=" * 65)
    print(f"🎯 场景：大模型一次性并行返回了 {len(cities)} 个城市的查询指令")
    print("=" * 65)

    # 1. 传统串行方式 (单线程同步等待)
    print("\n🐢 1. 传统同步串行执行:")
    start_time = time.time()
    serial_results = []
    for city in cities:
        # 串行等待
        res = await mock_remote_api(city)
        serial_results.append(res)
    serial_duration = time.time() - start_time
    print(f"❌ 串行总耗时: {serial_duration:.2f} 秒 (耗时随调用数量线性倍增)")

    # 2. 现代 Asyncio 并发方式
    print("\n🚀 2. 现代 Asyncio 并发一网打尽 (asyncio.gather):")
    start_time = time.time()
    # 同时发射所有协程任务
    parallel_tasks = [mock_remote_api(city) for city in cities]
    parallel_results = await asyncio.gather(*parallel_tasks)
    parallel_duration = time.time() - start_time
    print(f"⚡ 并发总耗时: {parallel_duration:.2f} 秒 (总耗时仅取决于单次最慢的请求！)")
    print(f"🎉 性能提升: {serial_duration / parallel_duration:.1f} 倍！")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(test_parallel_vs_serial())
