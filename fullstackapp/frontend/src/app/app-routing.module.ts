import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ArticlesComponent } from './articles/articles.component';
import { ArticleDetailComponent } from './article-detail/article-detail.component';
import { AdminComponent } from './admin/admin.component';
import { NotFoundComponent } from './not-found/not-found.component';
import { ArticleExistsGuard } from './guards/article-exists.guard';

const routes: Routes = [
  { path: '', redirectTo: '/articles', pathMatch: 'full' }, // Default route
  { path: 'articles', component: ArticlesComponent }, // Articles list
  { path: 'admin', component: AdminComponent }, // Admin dashboard
  {
    path: 'articles/:thread_id',
    component: ArticleDetailComponent,
    canActivate: [ArticleExistsGuard], // Use guard to validate thread_id
  },
  { path: '**', component: NotFoundComponent }, // Wildcard route for 404
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule {}
