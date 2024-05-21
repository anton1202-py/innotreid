from django.urls import path

from . import views

urlpatterns = [
    # path('', views.database_home, name='database_home'),
    path('article_compare', views.article_compare,
         name='database_article_compare'),
    path('create', views.create, name='create'),
    path('<int:pk>',
         views.DatabaseDetailView.as_view(),
         name='database_detail'
         ),
    path('<int:pk>/update',
         views.DatabaseUpdateView.as_view(),
         name='database_update'
         ),
    path('<int:pk>/delete',
         views.DatabaseDeleteView.as_view(),
         name='database_delete'
         ),
    path('stock/',
         views.database_stock,
         name='database_stock'
         ),
    path('stock_create',
         views.create_stock,
         name='createstock'
         ),
    path('stock/<str:article_marketplace>',
         views.DatabaseStockDetailView.as_view(),
         name='stock_detail'
         ),
    path('stock/<int:pk>/update',
         views.DatabaseStockUpdateView.as_view(),
         name='stock_update'
         ),
    path('stock/<int:pk>/delete',
         views.DatabaseStockDeleteView.as_view(),
         name='stock_delete'
         ),

    path('stock_wb/',
         views.database_stock_wb,
         name='stock_wb'
         ),
    path('createshelving',
         views.create_shelving_stocks,
         name='createshelving'
         ),
    path('stock_shelving/',
         views.database_stock_shelving,
         name='stock_shelving'
         ),
    path('stock_shelving/<int:pk>',
         views.DatabaseShelvingUpdateView.as_view(),
         name='stock_shelving_update'
         ),
    path('stock_frontend/',
         views.stock_frontend,
         name='stock_frontend'
         ),
    path('stock_frontend//<str:seller_article_wb>',
         views.DatabaseStockFrontendDetailView.as_view(),
         name='stock_frontend_detail'
         ),
    path('sales/',
         views.database_sales,
         name='database_sales'
         ),
    path('sales_create',
         views.create_sales,
         name='createsales'
         ),
    path('sales/<str:article_marketplace>',
         views.DatabaseSalesDetailView.as_view(),
         name='sales_detail'
         ),
    path('sales/<int:pk>/update',
         views.DatabaseSalesUpdateView.as_view(),
         name='sales_update'
         ),
    path('sales/<int:pk>/delete',
         views.DatabaseSalesDeleteView.as_view(),
         name='sales_delete'
         ),
    path('sales_analytic/',
         views.analytic_sales_data,
         name='sales_analytic'
         ),
    path('sales_analytic/<str:article_marketplace>',
         views.DatabaseSalesAnalyticDetailView.as_view(),
         name='sales_analytic_detail'
         ),
    path('orders_fbs/',
         views.database_orders_fbs,
         name='orders_fbs'
         ),
    path('login/', views.user_login, name='login'),
    path('logout/', views.logout_user, name='logout'),
]
