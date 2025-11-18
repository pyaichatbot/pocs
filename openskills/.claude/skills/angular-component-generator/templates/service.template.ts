import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class {{ComponentNamePascal}}Service {
  constructor(private http: HttpClient) {}

  // Example API call
  getData(params?: any): Observable<any> {
    return this.http.get('/api/{{component-name-kebab}}', { params });
  }
}
