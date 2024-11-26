import { TestBed } from '@angular/core/testing';

import { ArticleExistsGuard } from './article-exists.guard';

describe('ArticleExistsGuard', () => {
  let guard: ArticleExistsGuard;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    guard = TestBed.inject(ArticleExistsGuard);
  });

  it('should be created', () => {
    expect(guard).toBeTruthy();
  });
});
