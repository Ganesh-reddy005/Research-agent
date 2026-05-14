# Lume.ai - Development Status & Next Steps

## ✅ Completed Tasks
1.  **Rebranding:** Officially renamed the product to **Lume.ai**.
2.  **Modular Frontend:** Landing page split into reusable components (`Navbar`, `Hero`, `ValueProp`, `Features`, `CTA`, `Footer`).
3.  **UI Redesign:** 
    *   **Landing Page:** Elicit-inspired, professional scholarly aesthetic with cinematic hero.
    *   **Dashboard:** Sharp, rectangular, high-density layout. Added typing animation and mode dropdown to search.
4.  **Auth System:** 
    *   Supabase integration complete.
    *   `AuthModal.tsx` implemented with Google and Magic Link support.
5.  **Persistence Layer:** 
    *   `supabase_schema.sql` created and ready for deployment.
    *   `backend/graph/workflow.py` refactored to use `PostgresSaver` for permanent session memory.
6.  **Backend User-Session Mapping:**
    *   FastAPI routes updated to require Supabase JWT.
    *   LangGraph `thread_id` linked to `user_id` in `sessions` table.
7.  **Phase 1 Pivot (Private Library):**
    *   Implemented PDF-to-Qdrant ingestion pipeline.
    *   Added `LibraryPanel` with file upload and sovereign storage.
    *   Integrated private library search into the `RetrieverAgent`.

## 🚀 Immediate Next Steps (Pending)
1.  **Visual Citation Graph:**
    *   Integrate `react-flow` into the Research stage to show real-time paper connections.
2.  **LaTeX Export:**
    *   Implement Pandoc/LaTeX backend service for professional manuscript output.

## 🔑 Environment Variables Required
### Frontend (`.env.local`)
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### Backend (`.env`)
- `DATABASE_URL` (Supabase connection string with password)
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
