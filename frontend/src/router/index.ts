import { createRouter, createWebHistory } from "vue-router";
import { useWorkspaceStore } from "../stores/workspaceStore";
import WorkspaceView from "../views/WorkspaceView.vue";
import ProductLibraryView from "../views/ProductLibraryView.vue";

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
    }
  ]
});

router.beforeEach((to, from) => {
  if (to.fullPath === from.fullPath) {
    return true;
  }
  const workspace = useWorkspaceStore();
  return workspace.canLeaveActiveProject();
});

export default router;
