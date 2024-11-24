import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-article-detail',
  templateUrl: './article-detail.component.html',
  styleUrls: ['./article-detail.component.css'],
})
export class ArticleDetailComponent implements OnInit {
  article: any = null;

  constructor(private route: ActivatedRoute, private apiService: ApiService) {}

  async ngOnInit() {
    const threadId = this.route.snapshot.paramMap.get('thread_id');
    const sessions = await this.apiService.listSessions();
    this.article = sessions.find((session) => session.thread_id === threadId);
  }
}
