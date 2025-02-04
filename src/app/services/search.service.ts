import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SearchService {
  private resultsSubject = new BehaviorSubject<any>(null);
  results$ = this.resultsSubject.asObservable();
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  search(query: string, archives: string[]): Observable<any> {
    return this.http.post(`${this.apiUrl}/api/search`, {
      query,
      archives
    });
  }

  updateResults(results: any) {
    this.resultsSubject.next(results);
  }
} 