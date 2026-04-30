import { createRouter, createWebHistory } from "vue-router";
import { useWorkspaceStore } from "../stores/workspaceStore";
import WorkspaceView from "../views/WorkspaceView.vue";
import ProductLibraryView from "../views/ProductLibraryView.vue";
import PrintPreviewView from "../views/PrintPreviewView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "workspace",
      component: WorkspaceView
    },
    {
      path: "/products",
      name: "products",
      component: ProductLibraryView
    },
    {
      path: "/print",
      name: "print",
      component: PrintPreviewView
    }
  ]
});

router.beforeEach((to, from) => {
  if (to.fullPath === from.fullPath) {
    return true;
  }
  if (from.name !== "workspace" || to.name === "workspace") {
    return true;
  }
  const workspace = useWorkspaceStore();
  return workspace.canLeaveActiveProject();
});

export default router;
