# Build Directory Cleanup

## `.next` Directory

**Location**: `app/frontend/.next`
**Size**: ~23MB
**Status**: ✅ Already in `.gitignore` (line 15)

### What is `.next`?
- Next.js build output directory
- Contains compiled pages, static assets, and cache
- Automatically generated when you run `npm run dev` or `npm run build`
- Should **NEVER** be committed to git

### Current Status:
✅ **Properly ignored** - Not tracked by git
✅ **Can be safely deleted** - Will be regenerated on next build

### To Clean Up:

```bash
# Remove .next directory (will be regenerated on next dev/build)
rm -rf app/frontend/.next

# Or clean and rebuild
cd app/frontend
rm -rf .next
npm run dev  # Will regenerate .next
```

### Other Build Directories to Check:

- `app/frontend/.next/` - ✅ Ignored
- `app/frontend/node_modules/` - ✅ Ignored  
- `backend/__pycache__/` - ✅ Ignored
- `backend/*.pyc` - ✅ Ignored

All build artifacts are properly ignored!

