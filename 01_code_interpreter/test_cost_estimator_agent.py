#!/usr/bin/env python3
"""Simple test for AWS Cost Estimation Agent"""

import asyncio  # 非同期処理用（複数の処理を同時実行）
import argparse  # コマンドライン引数の解析用
from cost_estimator_agent.cost_estimator_agent import AWSCostEstimatorAgent


# ============================================================
# ストリーミングテスト（データを少しずつ受け取る）
# ============================================================
async def test_streaming(architecture: str, verbose: bool = True):
    """Test streaming cost estimation following Strands best practices"""
    if verbose:
        print("\n🔄 Testing streaming cost estimation...")
    agent = AWSCostEstimatorAgent()

    try:
        total_chunks = 0  # データの塊の数
        total_length = 0  # 受信した文字数

        # 🔑 重要: async forで非同期にデータを少しずつ受信
        async for event in agent.estimate_costs_stream(architecture):
            if "data" in event:  # データが含まれているか確認
                chunk_data = str(event["data"])
                if verbose:
                    print(chunk_data, end="", flush=True)  # 即座に表示

                total_chunks += 1
                total_length += len(chunk_data)

            elif "error" in event:  # エラーの場合
                if verbose:
                    print(f"\n❌ Streaming error: {event['data']}")
                return False

        if verbose:
            print(f"\n📊 Streaming completed: {total_chunks} chunks, {total_length} total characters")
        return total_length > 0  # データを受信できたらTrue

    except Exception as e:
        if verbose:
            print(f"❌ Streaming test failed: {e}")
        return False


# ============================================================
# 通常テスト（データを一括取得）
# ============================================================
def test_regular(architecture: str = "One EC2 t3.micro instance running 24/7", verbose: bool = True):
    """Test regular (non-streaming) cost estimation"""
    if verbose:
        print("📄 Testing regular cost estimation...")
    agent = AWSCostEstimatorAgent()

    try:
        # 🔑 重要: 一括でデータを取得
        result = agent.estimate_costs(architecture)
        if verbose:
            print(f"📊 Regular response length: {len(result)} characters")
            print(f"Result preview: {result[:150]}...")  # 最初の150文字を表示
        return len(result) > 0  # データがあればTrue
    except Exception as e:
        if verbose:
            print(f"❌ Regular test failed: {e}")
        return False


# ============================================================
# コマンドライン引数の設定
# ============================================================
def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Test AWS Cost Estimation Agent')

    # テストするアーキテクチャを指定
    parser.add_argument(
        '--architecture',
        type=str,
        default="One EC2 t3.micro instance running 24/7",
        help='Architecture description to test (default: "One EC2 t3.micro instance running 24/7")'
    )

    # 実行するテストの種類を指定（複数選択可）
    parser.add_argument(
        '--tests',
        nargs='+',  # 複数指定可能
        choices=['regular', 'streaming', 'debug'],
        default=['regular'],
        help='Which tests to run (default: regular)'
    )

    # 詳細表示のON/OFF
    parser.add_argument(
        '--verbose',
        action='store_true',
        default=True,
        help='Enable verbose output (default: True)'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Disable verbose output'
    )

    return parser.parse_args()


# ============================================================
# メイン処理（全体の制御）
# ============================================================
async def main():
    # 引数を解析
    args = parse_arguments()

    # verboseフラグの決定（verboseがTrueかつquietがFalseの場合のみTrue）
    verbose = args.verbose and not args.quiet

    print("🚀 Testing AWS Cost Agent")
    if verbose:
        print(f"Architecture: {args.architecture}")
        print(f"Tests to run: {', '.join(args.tests)}")

    # 🔑 重要: テスト結果を格納する辞書
    results = {}

    # 選択されたテストを実行
    if 'regular' in args.tests:
        results['regular'] = test_regular(args.architecture, verbose)

    if 'streaming' in args.tests:
        # 🔑 重要: 非同期関数なのでawaitが必要
        results['streaming'] = await test_streaming(args.architecture, verbose)

    # 結果を表示
    if verbose:
        print("\n📋 Test Results:")
        for test_name, success in results.items():
            status = '✅ PASS' if success else '❌ FAIL'
            print(f"   {test_name.capitalize()} implementation: {status}")

        # 🔑 重要: all()ですべてのテストが成功したかチェック
        if all(results.values()):
            print("🎉 All tests completed successfully!")
        else:
            print("⚠️ Some tests failed - check logs above")

    # 終了コード: 成功=0、失敗=1
    return 0 if all(results.values()) else 1


# ============================================================
# プログラムのエントリーポイント
# ============================================================
if __name__ == "__main__":
    import sys

    # 🔑 重要: asyncio.run()で非同期関数を実行
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
