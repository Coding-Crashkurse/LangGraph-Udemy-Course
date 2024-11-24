import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ArticlesComponent } from './articles/articles.component';
import { ArticleDetailComponent } from './article-detail/article-detail.component';
import { AdminComponent } from './admin/admin.component';

const routes: Routes = [
  { path: '', redirectTo: '/articles', pathMatch: 'full' }, // Default route
  { path: 'articles', component: ArticlesComponent }, // Articles list
  { path: 'articles/:thread_id', component: ArticleDetailComponent }, // Detailed article view
  { path: 'admin', component: AdminComponent }, // Admin dashboard
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule {}
