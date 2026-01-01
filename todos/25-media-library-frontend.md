# Media Library Frontend UI

## Status

⏸️ **BLOCKED** - Waiting for backend media upload implementation (Plan: groovy-hugging-planet)

## Problem

The backend now supports media file uploads via REST API, but there's no user-friendly way to upload and manage media files from the frontend. Users need a dedicated media library UI to:
- Upload media files (images, videos, audio) via drag-and-drop
- Browse uploaded media files with thumbnails/previews
- Copy media URLs to use in slide `media_url` fields
- Search and filter media files

Currently, users must either:
- Use the Django admin interface (not user-friendly)
- Manually construct file paths to reference uploaded media
- Use external URLs only

## Current State

**Backend** (`/home/aaron/projects/quizzer/service/`):
- MediaFile model exists with upload support
- API endpoints available:
  - `POST /api/media/upload/` - Upload file
  - `GET /api/media/` - List files
- Files stored in `/media/uploads/%Y/%m/`

**Frontend** (`/home/aaron/projects/quizzer/app/src/`):
- No media upload UI components
- No API client functions for media endpoints
- Slides display media via `media_url` but no way to populate it with uploaded files

## Proposed Solution

Create a frontend media library with:

1. **API Client Functions** (`app/src/lib/api.ts`):
   ```typescript
   uploadMedia(file: File): Promise<MediaFile>
   listMedia(): Promise<MediaFile[]>
   ```

2. **MediaUpload Component** (`app/src/lib/components/MediaUpload.svelte`):
   - Drag-and-drop file upload zone
   - File type and size validation
   - Upload progress indicator
   - Error handling

3. **MediaLibrary Component** (`app/src/lib/components/MediaLibrary.svelte`):
   - Grid view of uploaded files with thumbnails
   - Search/filter functionality
   - Click to copy URL to clipboard
   - Visual indication of file type (image/video/audio icons)
   - File size and upload date display

4. **Media Library Page** (`app/src/routes/media/+page.svelte`):
   - Standalone page at `/media`
   - Uses MediaLibrary component
   - Host-only access (requires auth check when implemented)

## Implementation Tasks

### Phase 1: API Client
- [ ] Add `uploadMedia()` function to `app/src/lib/api.ts`
- [ ] Add `listMedia()` function to `app/src/lib/api.ts`
- [ ] Add TypeScript interface for MediaFile response

### Phase 2: Upload Component
- [ ] Create `MediaUpload.svelte` component
- [ ] Implement drag-and-drop file upload
- [ ] Add client-side file validation (type, size)
- [ ] Show upload progress
- [ ] Display success/error messages

### Phase 3: Library Component
- [ ] Create `MediaLibrary.svelte` component
- [ ] Display uploaded files in grid layout
- [ ] Show thumbnails for images (use URL directly)
- [ ] Show file type icons for video/audio
- [ ] Add search/filter functionality
- [ ] Implement copy-to-clipboard for URLs
- [ ] Add file metadata display (size, date)

### Phase 4: Route & Integration
- [ ] Create `/media` route page
- [ ] Add navigation link to media library
- [ ] Add responsive design for mobile/tablet
- [ ] Consider modal/inline mode for slide editor integration

### Phase 5: Testing
- [ ] Unit tests for API client functions
- [ ] Component tests for MediaUpload
- [ ] Component tests for MediaLibrary
- [ ] E2E test: Upload → browse → copy URL → create slide → verify display

## Design Considerations

**File Upload UX:**
- Drag-and-drop should be primary interaction
- Fall back to file picker button
- Show visual feedback during drag-over
- Display upload progress percentage
- Clear success/error states

**Media Grid:**
- Thumbnail size: ~150-200px
- Lazy load images for performance
- Infinite scroll or pagination for large libraries
- Responsive grid (1-4 columns based on screen size)

**URL Copy:**
- One-click copy to clipboard
- Visual confirmation (toast or checkmark)
- Show full URL on hover

**Future Enhancements:**
- Multi-file upload
- Delete files (when DELETE API is added)
- Edit original filename
- Track which questions use each media file
- Bulk operations (select multiple, delete multiple)

## Technical Notes

**MediaFile Interface:**
```typescript
interface MediaFile {
  id: number;
  url: string;
  original_filename: string;
  file_size: number;
  uploaded_at: string;
}
```

**File Size Display:**
- Format bytes as KB/MB for readability
- Example: 2456789 → "2.3 MB"

**Thumbnail Strategy:**
- Images: Use URL directly in `<img>` tag
- Videos: Use video poster frame or generic video icon
- Audio: Use generic audio icon

## Dependencies

No new dependencies required - use native browser APIs:
- File API for file uploads
- Clipboard API for copy-to-clipboard
- Drag and Drop API

## Testing Philosophy

Following [TESTING.md](../TESTING.md):
- Focus on complex interactions (drag-drop, upload flow, error handling)
- Test behavior, not implementation
- Mock fetch calls in unit tests
- Use E2E tests for full upload-to-display flow

## References

- Backend implementation plan: groovy-hugging-planet.md
- Related models: service/game/models.py (MediaFile)
- API endpoints: service/game/views.py
