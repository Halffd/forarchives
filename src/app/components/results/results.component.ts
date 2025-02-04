import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SearchService } from '../../services/search.service';
import {
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardSubtitle,
  IonCardContent,
  IonButton,
  IonList,
  IonItem,
  IonLabel,
  IonBadge
} from '@ionic/angular/standalone';

@Component({
  selector: 'app-results',
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    IonCard,
    IonCardHeader,
    IonCardTitle,
    IonCardSubtitle,
    IonCardContent,
    IonButton,
    IonList,
    IonItem,
    IonLabel,
    IonBadge
  ]
})
export class ResultsComponent implements OnInit {
  results: any[] = [];
  siteCounts: any[] = [];
  displayedColumns: string[] = ['count', 'site'];

  constructor(private searchService: SearchService) {}

  ngOnInit() {
    this.searchService.results$.subscribe(data => {
      if (data?.results) {
        this.processResults(data.results);
      }
    });
  }

  private processResults(results: any[]) {
    // Reset arrays
    this.results = [];
    this.siteCounts = [];
    
    // Track sites and their counts
    const siteCountMap = new Map<string, number>();
    let lastSite = '';

    results.forEach(resultObj => {
      for (const key in resultObj) {
        const post = resultObj[key];
        
        if (!post) continue;

        // Handle source tracking
        if (key === 'source' && typeof post === 'string' && lastSite !== post) {
          lastSite = post;
          siteCountMap.set(lastSite, (siteCountMap.get(lastSite) || 0) + 1);
          continue;
        }

        // Skip if post is just a string (source) or doesn't have required properties
        if (typeof post !== 'object' || !post.num) continue;

        this.results.push({
          ...post,
          source: lastSite
        });
      }
    });

    // Convert site counts to array format for mat-table
    this.siteCounts = Array.from(siteCountMap.entries())
      .map(([site, count]) => ({ site, count }))
      .sort((a, b) => b.count - a.count);
  }
} 