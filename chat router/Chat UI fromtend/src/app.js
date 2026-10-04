import { installSameOriginChatBridge } from "./plugins/same-origin-chat.js";
import { createChatContext } from "./context.js";

import { readTypography } from "./typography/state.js";
import { applyTypography } from "./typography/apply.js";

installSameOriginChatBridge();

const context = createChatContext(document.getElementById("app"), document.getElementById("status"));
applyTypography(readTypography());
context.refresh();
