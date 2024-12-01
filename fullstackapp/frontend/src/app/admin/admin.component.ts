import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router'; // Import Router
import { ApiService } from '../api.service';
import { AuthService } from '../auth.service'; // Import AuthService

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css'],
})
export class AdminComponent implements OnInit {
  articles: any[] = [];
  editingArticleId: string | null = null;
  newAnswer: string = ''; // Ensure this is initialized as a string

  constructor(
    private apiService: ApiService,
    private authService: AuthService,
    private router: Router
  ) {} // Inject AuthService and Router

  async ngOnInit() {
    const allArticles = await this.apiService.listSessions();
    this.articles = allArticles.filter(
      (article) => article.question && article.answer
    );
  }

  async deleteArticle(threadId: string) {
    await this.apiService.deleteThread(threadId);
    this.articles = this.articles.filter(
      (article) => article.thread_id !== threadId
    );
  }

  async confirmArticle(threadId: string) {
    const updatedArticle = await this.apiService.confirmThread(threadId);
    const index = this.articles.findIndex(
      (article) => article.thread_id === threadId
    );
    if (index !== -1) {
      this.articles[index] = updatedArticle;
    }
  }

  startEditing(threadId: string, currentAnswer: string) {
    this.editingArticleId = threadId;
    this.newAnswer = currentAnswer;
  }

  cancelEditing() {
    this.editingArticleId = null;
    this.newAnswer = '';
  }

  async saveEditedArticle(threadId: string) {
    const updatedArticle = await this.apiService.editThread(
      threadId,
      this.newAnswer
    );
    const index = this.articles.findIndex(
      (article) => article.thread_id === threadId
    );
    if (index !== -1) {
      this.articles[index] = updatedArticle;
    }
    this.editingArticleId = null;
    this.newAnswer = '';
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']); // Navigate to the login page after logout
  }
}
