import { createRouter, createWebHistory } from "vue-router";
import WorkspaceView from "../views/WorkspaceView.vue";
import ProductLibraryView from "../views/ProductLibraryView.vue";

export default createRouter({
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
