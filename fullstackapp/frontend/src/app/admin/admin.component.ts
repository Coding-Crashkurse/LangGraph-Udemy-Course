import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service'; // Import the ApiService

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css'],
})
export class AdminComponent implements OnInit {
  articles: any[] = [];

  constructor(private apiService: ApiService) {} // Inject the ApiService

  async ngOnInit() {
    this.articles = await this.apiService.listSessions(); // Use ApiService to fetch data
  }

  async deleteArticle(threadId: string) {
    await this.apiService.deleteThread(threadId); // Call deleteThread from ApiService
    this.articles = this.articles.filter(
      (article) => article.thread_id !== threadId
    );
  }

  async confirmArticle(threadId: string) {
    const updatedArticle = await this.apiService.confirmThread(threadId); // Call confirmThread
    const index = this.articles.findIndex(
      (article) => article.thread_id === threadId
    );
    if (index !== -1) {
      this.articles[index] = updatedArticle;
    }
  }
}
