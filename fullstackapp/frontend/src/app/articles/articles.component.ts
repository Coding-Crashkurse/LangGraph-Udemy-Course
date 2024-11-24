import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-articles',
  templateUrl: './articles.component.html',
  styleUrls: ['./articles.component.css'],
})
export class ArticlesComponent implements OnInit {
  articles: any[] = [];

  constructor(private apiService: ApiService, private router: Router) {}

  async ngOnInit() {
    const sessions = await this.apiService.listSessions();
    this.articles = sessions.filter((session) => session.confirmed === true);
  }

  viewArticle(threadId: string) {
    this.router.navigate(['/articles', threadId]);
  }
}
