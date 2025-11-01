import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface User {
  id?: string;
  username: string;
  email: string;
  phone_number?: string;
  is_active?: boolean;
  created_at?: string;
}

export interface EnrollmentRequest {
  username: string;
  email: string;
  phone_number?: string;
  audio_data: string; // Base64 encoded audio
}

export interface AuthenticationRequest {
  username: string;
  audio_data: string; // Base64 encoded audio
}

export interface ChallengeResponse {
  challenge_id: string;
  challenge_text: string;
  expires_at: string;
}

export interface VerificationResponse {
  success: boolean;
  confidence_score: number;
  message: string;
  user_id?: string;
}

@Injectable({
  providedIn: 'root',
})
export class Api {
  private baseUrl = environment.apiUrl || 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    });
  }

  // Health check
  healthCheck(): Observable<any> {
    return this.http.get(`${this.baseUrl}/health`);
  }

  // User enrollment
  enrollUser(data: EnrollmentRequest): Observable<User> {
    return this.http.post<User>(`${this.baseUrl}/enrollment`, data, {
      headers: this.getHeaders()
    });
  }

  // Get challenge for authentication
  getChallenge(username: string): Observable<ChallengeResponse> {
    return this.http.post<ChallengeResponse>(`${this.baseUrl}/challenge`, 
      { username }, 
      { headers: this.getHeaders() }
    );
  }

  // Verify user authentication
  verifyUser(data: AuthenticationRequest): Observable<VerificationResponse> {
    return this.http.post<VerificationResponse>(`${this.baseUrl}/verification`, data, {
      headers: this.getHeaders()
    });
  }

  // Get all users (for dashboard)
  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(`${this.baseUrl}/users`, {
      headers: this.getHeaders()
    });
  }

  // Get user by ID
  getUser(userId: string): Observable<User> {
    return this.http.get<User>(`${this.baseUrl}/users/${userId}`, {
      headers: this.getHeaders()
    });
  }

  // Delete user
  deleteUser(userId: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/users/${userId}`, {
      headers: this.getHeaders()
    });
  }
}
