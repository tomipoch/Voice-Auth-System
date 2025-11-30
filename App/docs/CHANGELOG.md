# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Comprehensive testing infrastructure with Vitest and React Testing Library
- 14 unit and integration tests with 100% pass rate
- Git hooks with Husky and lint-staged for code quality automation
- CI/CD pipeline with GitHub Actions (lint, test, build, deploy)
- Complete project documentation (README, TESTING, GIT_HOOKS, CI_CD, CONTRIBUTING)
- ESLint and Prettier integration for consistent code formatting
- Code coverage reporting with Codecov integration

### Changed

- Updated README with comprehensive project information
- Improved dark mode implementation documentation
- Enhanced environment configuration documentation

## [1.0.0] - 2025-11-17

### Added

- Initial release of VoiceAuth
- Voice biometric authentication system
- User registration with voice enrollment
- Voice verification functionality
- Multi-role system (User, Admin, Super Admin)
- Admin dashboard with user management
- System metrics and statistics
- Dark mode with localStorage persistence
- Responsive UI with Tailwind CSS 4.1.17
- Mock API for development
- Environment-based configuration (dev, staging, prod)
- Audio recording with quality analysis
- JWT token authentication with refresh
- Protected routes with role-based access
- Settings management
- Theme switching (light/dark/system)

### Technical Stack

- React 19.2.0
- Vite 7.2.2 (rolldown-vite)
- React Router 7.9.6
- Tailwind CSS 4.1.17
- Axios 1.7.9
- Lucide React for icons
- TanStack Query for state management

### Components

- Authentication forms (Login, Register)
- Voice enrollment wizard with 3-step process
- Voice verification interface
- Admin panels (User Management, System Metrics)
- Reusable UI components (Button, Card, Input, Modal, etc.)
- Audio recorder with visual feedback
- Status indicators
- Navigation sidebar
- Main layout with theme support

### Services

- API client with interceptors
- Mock API with realistic data
- Storage service with localStorage abstraction
- Authentication service
- Environment configuration service

### Documentation

- LOGIN_SYSTEM.md - Authentication implementation
- DARK_MODE_IMPLEMENTATION.md - Theme system
- ENVIRONMENTS.md - Environment configuration
- CODE_FORMAT.md - Code style guide

### Security

- JWT token management
- Secure storage with prefixes
- Input validation
- Protected API routes
- Role-based access control

## [0.1.0] - 2025-11-01

### Added

- Initial project setup
- Basic React + Vite configuration
- Tailwind CSS integration
- ESLint configuration
- Project structure

---

## Version History Notes

### Versioning Scheme

We use [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

### Categories

- **Added** - New features
- **Changed** - Changes in existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Vulnerability fixes

### Links

- [Unreleased]: https://github.com/tomipoch/Proyecto/compare/v1.0.0...HEAD
- [1.0.0]: https://github.com/tomipoch/Proyecto/releases/tag/v1.0.0
- [0.1.0]: https://github.com/tomipoch/Proyecto/releases/tag/v0.1.0
