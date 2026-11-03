# Android conversation-first redesign

Historical direction, superseded by MOBILE_DIRECTION_V3.md after the user requested a less generic finish.

Mode: Operate. User explicitly rejected the large index/cards and selected Gemini as the closer reference. English and Konecto lilac remain; scope stays strictly within the assessment.

## Direction contract

THESIS: The conversation is the workspace. Saved conversations are a compact left drawer, not the landing dashboard. The user confirmed chat-first startup and history on the left.

OWN-WORLD: Near-white #FAFAFC canvas, softly neutral #EFEEF4 composer/drawer, charcoal text, dark plum #4C315E actions and a restrained lilac selection. Native Material type and controls. No giant Conversations heading, decorative monogram, gradient, avatar, model selector, tools/voice/attachment controls or unrelated destinations.

STORY: Arrive at the empty chat, type or fill a starter prompt, consult technical results, open the left menu to resume a saved session. Developer-only trace access belongs in the drawer, never the end-user toolbar.

FIRST VIEWPORT: Compact left-aligned Series 76 app-bar title with hamburger and new-chat action. Left-aligned Hello./How can I help? greeting near upper-middle, domain subtitle, two compact tonal shortcut pills. A broad tonal rounded composer sits at the bottom above native insets. In a populated chat, the greeting gives way to messages and an outlined technical result. Drawer is about 82% of a compact phone width; rows have title/date with a selected highlight and a New chat pill.

FORM: User-pinned Gemini-inspired native conversation shell; seed 67e85cdc. Approved mockup gemini-home.png and gemini-drawer.png in .impeccable/mocks/redesign-v2. User said: 'Apruebo esta versión tipo Gemini y sus adaptaciones nativas' in response to a question explicitly stating no pixel-for-pixel clone was required. Native typography, real OS bars, responsive text and dynamic history may differ from image pixels; the layout hierarchy and component character govern.

INTERACTION: Native ModalNavigationDrawer: scrim, dismiss gesture and system Back close it without losing session/draft. Opening history refreshes the existing list. Selecting a saved conversation retains backend context and closes the drawer. Two starter actions fill the draft and focus the existing composer; they never send automatically or create capabilities. One pending send blocks switching/new-chat. Compose motion respects Android animation scale.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Truth and bounds

The catalogue/backend are unchanged by this redesign. Preserve full codes, units, frequency, service, N/A and notes; preserve comparison semantics and release/debug separation. Test against current API35 phone emulator with keyboard, drawer, errors and font130 captures. No fake app records or answers. Mockup history is illustrative only. No Android UI raster assets ship; all controls and text are Compose.
