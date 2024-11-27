import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, Router } from '@angular/router';
import { Observable, lastValueFrom } from 'rxjs';
import { ApiService } from '../api.service';

@Injectable({
  providedIn: 'root',
})
export class ArticleExistsGuard implements CanActivate {
  constructor(private apiService: ApiService, private router: Router) {}

  async canActivate(route: ActivatedRouteSnapshot): Promise<boolean> {
    const threadId = route.paramMap.get('thread_id');
    if (!threadId) {
      this.router.navigate(['/404']);
      return false;
    }

    try {
      // Use lastValueFrom to await the Observable
      const session = await lastValueFrom(
        this.apiService.getSessionById(threadId)
      );
      if (session) {
        return true; // Allow navigation if session exists
      } else {
        this.router.navigate(['/404']);
        return false;
      }
    } catch (error) {
      this.router.navigate(['/404']);
      return false;
    }
  }
}
