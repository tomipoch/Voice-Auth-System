import { Routes } from '@angular/router';
import { Enrollment } from './components/enrollment/enrollment';
import { Authentication } from './components/authentication/authentication';
import { Dashboard } from './components/dashboard/dashboard';

export const routes: Routes = [
  { path: '', redirectTo: '/authentication', pathMatch: 'full' },
  { path: 'authentication', component: Authentication },
  { path: 'enrollment', component: Enrollment },
  { path: 'dashboard', component: Dashboard },
  { path: '**', redirectTo: '/authentication' }
];
