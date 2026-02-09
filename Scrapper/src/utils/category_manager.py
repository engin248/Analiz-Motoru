"""
Kategori Yönetim Sistemi
- categories.json dosyasını okur
- VPS'lere göre kategorileri filtreler
- Önceliklendirme yapar
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from rich.console import Console

console = Console()

class CategoryManager:
    def __init__(self, config_path: str = "categories.json"):
        self.config_path = config_path
        self.categories = []
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """categories.json dosyasını yükle"""
        if not os.path.exists(self.config_path):
            console.print(f"[red]❌ {self.config_path} bulunamadı![/red]")
            raise FileNotFoundError(f"{self.config_path} not found")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.categories = data.get('categories', [])
            self.config = data.get('config', {})
        
        console.print(f"[green]✅ {len(self.categories)} kategori yüklendi[/green]")
    
    def get_categories_for_vps(self, vps_id: int) -> List[Dict]:
        """
        Belirtilen VPS için kategorileri döndür
        
        Args:
            vps_id: VPS numarası (1, 2, 3)
        
        Returns:
            Bu VPS'e atanmış ve enabled=true olan kategoriler
        """
        return [
            cat for cat in self.categories 
            if cat.get('vps_id') == vps_id and cat.get('enabled', True)
        ]
    
    def get_all_enabled_categories(self) -> List[Dict]:
        """Tüm aktif kategorileri döndür"""
        return [cat for cat in self.categories if cat.get('enabled', True)]
    
    def get_category_by_id(self, category_id: int) -> Optional[Dict]:
        """ID'ye göre kategori döndür"""
        for cat in self.categories:
            if cat.get('id') == category_id:
                return cat
        return None
    
    def get_categories_by_priority(self, priority: str) -> List[Dict]:
        """
        Önceliğe göre kategorileri filtrele
        
        Args:
            priority: 'high', 'medium', 'low'
        """
        return [
            cat for cat in self.categories 
            if cat.get('priority') == priority and cat.get('enabled', True)
        ]
    
    def get_total_expected_links(self) -> int:
        """
        Tüm kategorilerden beklenen toplam link sayısı
        Formül: sum(max_pages × 24 ürün/sayfa)
        """
        total = 0
        for cat in self.get_all_enabled_categories():
            max_pages = cat.get('max_pages', 200)
            total += max_pages * 24  # Ortalama 24 ürün/sayfa
        return total
    
    def print_summary(self):
        """Kategori özetini yazdır"""
        enabled = self.get_all_enabled_categories()
        
        console.print("\n[bold cyan]📊 KATEGORİ ÖZETİ[/bold cyan]")
        console.print(f"Toplam Kategori: {len(self.categories)}")
        console.print(f"Aktif Kategori: {len(enabled)}")
        
        # VPS'lere göre dağılım
        vps_dist = {}
        for cat in enabled:
            vps_id = cat.get('vps_id', 0)
            vps_dist[vps_id] = vps_dist.get(vps_id, 0) + 1
        
        console.print("\n[cyan]VPS Dağılımı:[/cyan]")
        for vps_id, count in sorted(vps_dist.items()):
            console.print(f"  VPS {vps_id}: {count} kategori")
        
        # Öncelik dağılımı
        console.print("\n[cyan]Öncelik Dağılımı:[/cyan]")
        for priority in ['high', 'medium', 'low']:
            count = len(self.get_categories_by_priority(priority))
            console.print(f"  {priority.capitalize()}: {count} kategori")
        
        # Beklenen link sayısı
        total_links = self.get_total_expected_links()
        console.print(f"\n[bold green]📦 Beklenen Toplam Link: {total_links:,}[/bold green]\n")
    
    def export_daily_plan(self, vps_id: Optional[int] = None, output_file: str = "daily_plan.txt"):
        """
        Günlük çalışma planını dışa aktar
        
        Args:
            vps_id: Sadece belirli bir VPS için plan (None = tümü)
            output_file: Çıktı dosyası
        """
        if vps_id:
            categories = self.get_categories_for_vps(vps_id)
            title = f"VPS {vps_id} Günlük Plan"
        else:
            categories = self.get_all_enabled_categories()
            title = "Tüm VPS'ler için Günlük Plan"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"{title}\n")
            f.write(f"Oluşturulma: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, cat in enumerate(categories, 1):
                f.write(f"{i}. {cat['name']}\n")
                f.write(f"   Keyword: {cat['keyword']}\n")
                f.write(f"   Max Sayfa: {cat['max_pages']}\n")
                f.write(f"   Öncelik: {cat.get('priority', 'N/A')}\n")
                f.write(f"   Beklenen Link: {cat['max_pages'] * 24:,}\n")
                f.write("\n")
            
            f.write(f"\nToplam Kategori: {len(categories)}\n")
            total_links = sum(cat['max_pages'] * 24 for cat in categories)
            f.write(f"Toplam Beklenen Link: {total_links:,}\n")
        
        console.print(f"[green]✅ Plan dışa aktarıldı: {output_file}[/green]")


# Test & CLI Kullanım
if __name__ == "__main__":
    manager = CategoryManager()
    
    # Özet yazdır
    manager.print_summary()
    
    # VPS 1 için kategorileri göster
    console.print("\n[bold]VPS 1 Kategorileri:[/bold]")
    vps1_cats = manager.get_categories_for_vps(1)
    for cat in vps1_cats:
        console.print(f"  - {cat['name']} ({cat['keyword']})")
    
    # Günlük plan oluştur
    manager.export_daily_plan(vps_id=1, output_file="vps1_daily_plan.txt")
