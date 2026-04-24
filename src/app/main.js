import { createController } from "./controller.js";
import { getDomElements } from "../ui/dom.js";


const dom = getDomElements();
const controller = createController(dom);

controller.bindEvents();

async function bootstrap() {
  await controller.hydrateRuntime();
}

void bootstrap();
