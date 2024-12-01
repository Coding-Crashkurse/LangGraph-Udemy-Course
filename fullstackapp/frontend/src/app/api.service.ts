import { Injectable } from '@angular/core';
import { from, Observable } from 'rxjs';
import axios, { AxiosResponse } from 'axios';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private baseUrl = 'http://localhost:8000';

  async listSessions(): Promise<any[]> {
    const response: AxiosResponse = await axios.get(`${this.baseUrl}/sessions`);
    return response.data;
  }

  async deleteThread(threadId: string): Promise<void> {
    await axios.delete(`${this.baseUrl}/delete_thread/${threadId}`);
  }

  async confirmThread(threadId: string): Promise<any> {
    const response: AxiosResponse = await axios.post(
      `${this.baseUrl}/confirm/${threadId}`
    );
    return response.data;
  }

  async editThread(threadId: string, answer: string): Promise<any> {
    const response: AxiosResponse = await axios.patch(
      `${this.baseUrl}/edit_state/${threadId}`,
      { answer }
    );
    return response.data;
  }

  getSessionById(threadId: string): Observable<any> {
    return from(
      this.listSessions().then((sessions) =>
        sessions.find((session) => session.thread_id === threadId)
      )
    );
  }
}
