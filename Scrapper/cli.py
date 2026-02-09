"""
CLI - Command Line Interface for all scraper tools
Usage: python cli.py <command>
"""

import sys
import argparse
from rich.console import Console

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="🤖 Trendyol Scraper CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Komutlar:
  scrape      Scraper'ı çalıştır
  analyze     Veri analizi yap
  check       Son taranan ürünleri göster
  export      Verileri Excel'e aktar
  reset       Veritabanını sıfırla
  stats       Hızlı istatistikler

Örnek:
  python cli.py scrape
  python cli.py export rapor.xlsx
  python cli.py check --limit 50
        """
    )
    
    parser.add_argument('command', nargs='?', default='help',
                       choices=['scrape', 'analyze', 'check', 'export', 'reset', 'stats', 'help'],
                       help='Çalıştırılacak komut')
    parser.add_argument('--limit', type=int, default=20, help='Gösterilecek kayıt sayısı')
    parser.add_argument('--output', '-o', type=str, help='Çıktı dosya adı')
    
    args = parser.parse_args()
    
    if args.command == 'help' or len(sys.argv) == 1:
        parser.print_help()
        return
    
    if args.command == 'scrape':
        console.print("[cyan]🚀 Scraper başlatılıyor...[/cyan]")
        import asyncio
        from main import main as run_scraper
        asyncio.run(run_scraper())
        
    elif args.command == 'analyze':
        from tools.db_tools import analyze
        analyze()
        
    elif args.command == 'check':
        from tools.db_tools import check
        check(limit=args.limit)
        
    elif args.command == 'export':
        from tools.db_tools import export
        export(filename=args.output)
        
    elif args.command == 'reset':
        from tools.db_tools import reset
        reset()
        
    elif args.command == 'stats':
        from tools.db_tools import stats
        stats()


if __name__ == "__main__":
    main()
