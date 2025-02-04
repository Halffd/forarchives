import { Component } from '@angular/core';
import { SearchComponent } from './components/search/search.component';
import { ResultsComponent } from './components/results/results.component';
import { HttpClientModule } from '@angular/common/http';
import { IonApp, IonContent, IonHeader, IonTitle, IonToolbar } from '@ionic/angular/standalone';

@Component({
  selector: 'app-root',
  template: `
    <ion-app>
      <ion-header>
        <ion-toolbar color="primary">
          <ion-title>Archive Search</ion-title>
        </ion-toolbar>
      </ion-header>

      <ion-content>
        <div class="app-container">
          <app-search></app-search>
          <app-results></app-results>
        </div>
      </ion-content>
    </ion-app>
  `,
  standalone: true,
  imports: [
    SearchComponent, 
    ResultsComponent, 
    HttpClientModule,
    IonApp,
    IonContent,
    IonHeader,
    IonTitle,
    IonToolbar
  ]
})
export class AppComponent {}
