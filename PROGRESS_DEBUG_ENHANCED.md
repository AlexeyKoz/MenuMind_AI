# 🔧 DEBUGGING: Progress Bar Stuck at 10%

## Current Status

✅ **Modal closes** - Fallback is working
❌ **Progress stuck at 10%** - WebSocket messages not reaching frontend

---

## Enhanced Logging Added

### Backend (Terminal):

**Progress Tracker** - Now shows:
```
[PROGRESS] Sending to group: user_2ca03630-94a5-424a-bc9d-fa6ea883e37a
[PROGRESS] Stage: searching, Percent: 10, Message: Searching the internet...
[PROGRESS] ✅ Sent: 10% - Searching the internet...
```

**WebSocket Consumer** - Now shows:
```
📡 [CONSUMER] Received recipe_progress event for user testuser1
📡 [CONSUMER] Event data: {'stage': 'searching', 'percent': 10, 'message': '...'}
📡 [CONSUMER] Sending to WebSocket client...
📡 [CONSUMER] ✅ Sent progress update to client: 10%
```

### Frontend (Browser Console):

Already shows:
```
[PROGRESS] 📨 Raw WebSocket message received: ...
[PROGRESS] 🎯 Recipe progress update!
[PROGRESS] Stage: searching
[PROGRESS] Percent: 10
```

---

## Test Instructions

### 1. Clear Everything
```bash
# Browser:
- Clear cache (Ctrl+Shift+Delete)
- Hard refresh (Ctrl+F5)
- Open console (F12)
```

### 2. Generate a Recipe

Watch **THREE** places simultaneously:

#### A. Backend Console (Terminal)
Look for:
```
[PROGRESS] Sending to group: user_...
[PROGRESS] ✅ Sent: 10% - ...
📡 [CONSUMER] Received recipe_progress event...
📡 [CONSUMER] ✅ Sent progress update to client: 10%

[PROGRESS] Sending to group: user_...
[PROGRESS] ✅ Sent: 25% - ...
📡 [CONSUMER] Received recipe_progress event...
📡 [CONSUMER] ✅ Sent progress update to client: 25%
```

#### B. Frontend Console (Browser F12)
Look for:
```
[PROGRESS] ✅ WebSocket connected successfully!
[PROGRESS] 📨 Raw WebSocket message received: {"type":"recipe_progress",...}
[PROGRESS] 🎯 Recipe progress update!
[PROGRESS] Percent: 10

[PROGRESS] 📨 Raw WebSocket message received: {"type":"recipe_progress",...}
[PROGRESS] 🎯 Recipe progress update!
[PROGRESS] Percent: 25
```

#### C. Progress Modal (Visual)
Should see:
- Bar animates: 10% → 25% → 40% → 55% → 70% → 85% → 95% → 100%
- Messages change
- Checkmarks appear for completed stages

---

## Diagnostic Scenarios

### Scenario 1: Backend Sends, Consumer Receives, Frontend Doesn't

**Backend shows:**
```
[PROGRESS] ✅ Sent: 25% - ...
📡 [CONSUMER] ✅ Sent progress update to client: 25%
```

**Frontend shows:**
```
[PROGRESS] ✅ WebSocket connected!
(... no more messages ...)
```

**Problem:** WebSocket connected to WRONG user group or message format issue

**Solution:** Check user ID in group name matches

---

### Scenario 2: Backend Sends, Consumer Never Receives

**Backend shows:**
```
[PROGRESS] ✅ Sent: 25% - ...
(... no consumer logs ...)
```

**Problem:** Channel layer not working or consumer not in group

**Solution:** Check Redis/Channel layer configuration

---

### Scenario 3: Nothing in Backend

**Backend shows:**
```
[RECIPE AGENT] Processing query...
(... no [PROGRESS] logs ...)
```

**Problem:** Progress tracker not initialized or exception caught silently

**Solution:** Check if `progress = RecipeGenerationProgress(...)` is being called

---

### Scenario 4: WebSocket Connects After Messages Sent

**Timing:**
```
T+0s: Recipe generation starts → [PROGRESS] 10% sent
T+1s: WebSocket connects → [PROGRESS] ✅ WebSocket connected!
T+2s: [PROGRESS] 25% sent
```

**Problem:** First message (10%) sent before WebSocket connected

**Solution:** This is the LIKELY CAUSE! WebSocket needs to be connected BEFORE starting API call

---

## Likely Root Cause: Timing Issue

The WebSocket connection might be opening AFTER the first progress messages are sent!

### Current Flow (BROKEN):
```
1. User clicks search
2. setShowProgress(true) → Modal opens
3. useEffect runs → WebSocket starts connecting...
4. api.findRecipe() called immediately
5. Backend sends 10% → WebSocket still connecting! ❌
6. WebSocket finishes connecting
7. Backend sends 25%, 40%, etc. → WebSocket connected ✅
```

### What We Need (FIXED):
```
1. User clicks search
2. setShowProgress(true) → Modal opens
3. useEffect runs → WebSocket connects
4. WAIT for WebSocket to connect
5. THEN call api.findRecipe()
6. Backend sends 10% → WebSocket ready! ✅
```

---

## Quick Fix: Use Callback

**File:** `frontend/src/components/RecipeProgressModal.tsx`

Add a callback prop to notify when WebSocket is ready:

```typescript
interface RecipeProgressModalProps {
    isOpen: boolean;
    onClose: () => void;
    onWebSocketReady?: () => void; // NEW
}

// In useEffect:
ws.onopen = () => {
    console.log('[PROGRESS] ✅ WebSocket connected!');
    if (onWebSocketReady) {
        onWebSocketReady(); // Notify parent
    }
};
```

**File:** `frontend/src/pages/CanonicalRecipesPage.tsx`

Wait for WebSocket before calling API:

```typescript
const handleAISearch = async () => {
    setShowProgress(true);
    
    // Wait for WebSocket to connect
    await new Promise(resolve => {
        setWebSocketReadyCallback(() => resolve);
    });
    
    // Now make API call
    const result = await api.findRecipe(aiQuery);
};
```

---

## Even Simpler Fix: Add Delay

Add a small delay to ensure WebSocket connects first:

```typescript
const handleAISearch = async () => {
    setShowProgress(true);
    
    // Give WebSocket 500ms to connect
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const result = await api.findRecipe(aiQuery);
};
```

---

## Test & Report

**After testing, send me:**

1. **Backend console logs** - All `[PROGRESS]` and `📡 [CONSUMER]` lines
2. **Frontend console logs** - All `[PROGRESS]` lines
3. **What you saw** - Did the bar move? At what percentage?

This will tell us EXACTLY where the messages are getting lost!

---

## Backend Restarted!

✅ **Enhanced logging active**
✅ **Ready to test**

**Generate a recipe now and send me the logs from BOTH consoles!** 🔍

