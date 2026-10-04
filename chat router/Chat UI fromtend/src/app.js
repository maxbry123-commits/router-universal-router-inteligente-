import { installSameOriginChatBridge } from "./plugins/same-origin-chat.js";
import { createChatContext } from "./context.js";

installSameOriginChatBridge();
const context = createChatContext(document.getElementById("app"), document.getElementById("status"));
context.refresh();
