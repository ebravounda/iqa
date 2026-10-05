import { useState, useEffect, useMemo, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Package, Plus, ShoppingCart, Search, Tags, Edit, Trash2, Minus,
  DollarSign, BarChart3, Archive, AlertTriangle, X, Check, Save, Loader2,
  Camera, ImageIcon, Printer
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const DEFAULT_CATEGORIES = ['Bebidas', 'Suplementos', 'Ropa', 'Accesorios', 'Snacks', 'Servicios', 'General'];

export default function AdminPOS() {
  const { admin } = useAuth();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [cart, setCart] = useState([]);
  const [sales, setSales] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [activeTab, setActiveTab] = useState('pos');
  const [productForm, setProductForm] = useState({
    name: '', description: '', cost_price: 0, sale_price: 0, stock: 0, category: 'General', barcode: '', image_url: ''
  });
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [processing, setProcessing] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const fileInputRef = useRef(null);

  const gymId = admin?.gym_id;

  useEffect(() => { fetchData(true); }, []);

  const fetchData = async (initial = false) => {
    if (initial) setLoading(true);
    try {
      const params = gymId ? { gym_id: gymId } : {};
      const [prodRes, catRes, salesRes, statsRes] = await Promise.all([
        axios.get(`${API}/pos/products`, { params }),
        axios.get(`${API}/pos/categories`, { params }),
        axios.get(`${API}/pos/sales`, { params }),
        axios.get(`${API}/pos/stats`, { params })
      ]);
      setProducts(prodRes.data);
      setCategories(catRes.data);
      setSales(salesRes.data);
      setStats(statsRes.data);
    } catch { toast.error('Error al cargar datos'); }
    finally { if (initial) setLoading(false); }
  };

  const getImageUrl = (url) => {
    if (!url) return null;
    if (url.startsWith('/')) return `${process.env.REACT_APP_BACKEND_URL}${url}`;
    return url;
  };

  const filteredProducts = useMemo(() => {
    return products.filter(p => {
      const matchesSearch = !search || p.name.toLowerCase().includes(search.toLowerCase()) || (p.barcode || '').includes(search);
      const matchesCat = activeCategory === 'all' || (p.category || 'General').toLowerCase() === activeCategory.toLowerCase();
      return matchesSearch && matchesCat && p.active !== false;
    });
  }, [products, search, activeCategory]);

  const allCategories = useMemo(() => {
    const fromProducts = [...new Set(products.map(p => p.category || 'General'))];
    const merged = [...new Set([...fromProducts, ...categories])];
    return merged.sort();
  }, [products, categories]);

  const cartTotal = cart.reduce((sum, item) => sum + item.sale_price * item.qty, 0);
  const cartCount = cart.reduce((sum, item) => sum + item.qty, 0);

  const addToCart = (product) => {
    if (product.stock <= 0) { toast.error('Sin stock'); return; }
    setCart(prev => {
      const existing = prev.find(i => i.id === product.id);
      if (existing) {
        if (existing.qty >= product.stock) { toast.error('Stock insuficiente'); return prev; }
        return prev.map(i => i.id === product.id ? { ...i, qty: i.qty + 1 } : i);
      }
      return [...prev, { ...product, qty: 1 }];
    });
  };

  const updateCartQty = (productId, delta) => {
    setCart(prev => prev.map(i => {
      if (i.id !== productId) return i;
      const newQty = i.qty + delta;
      if (newQty <= 0) return null;
      if (newQty > i.stock) { toast.error('Stock insuficiente'); return i; }
      return { ...i, qty: newQty };
    }).filter(Boolean));
  };

  const processSale = async () => {
    if (cart.length === 0) return;
    const saleGymId = gymId || cart[0]?.gym_id;
    if (!saleGymId) { toast.error('No se pudo determinar el negocio'); return; }
    setProcessing(true);
    try {
      const res = await axios.post(`${API}/pos/sales`, {
        gym_id: saleGymId,
        items: cart.map(i => ({ product_id: i.id, quantity: i.qty, unit_price: i.sale_price })),
        total: cartTotal,
        currency: 'EUR',
        payment_method: paymentMethod
      });
      toast.success(`Venta procesada: $${cartTotal.toFixed(2)}`, {
        action: { label: 'Imprimir Ticket', onClick: () => printReceipt(res.data.sale || { items: cart.map(i => ({ product_name: i.name, quantity: i.qty, unit_price: i.sale_price })), total: cartTotal, payment_method: paymentMethod, created_at: new Date().toISOString(), id: res.data.sale?.id || '' }) },
        duration: 8000
      });
      setCart([]);
      fetchData();
    } catch (err) { toast.error(err.response?.data?.detail || 'Error al procesar venta'); }
    finally { setProcessing(false); }
  };

  const printReceipt = (sale, gymName) => {
    const businessName = gymName || admin?.gym_name || 'Mi Negocio';
    const date = sale.created_at ? new Date(sale.created_at).toLocaleString() : new Date().toLocaleString();
    const payMethod = sale.payment_method === 'cash' ? 'Efectivo' : sale.payment_method === 'card_reception' ? 'Tarjeta' : 'Transferencia';
    
    const itemsHtml = (sale.items || []).map(i => 
      `<tr>
        <td style="text-align:left;padding:2px 0">${i.quantity}x ${i.product_name || 'Producto'}</td>
        <td style="text-align:right;padding:2px 0">$${(i.unit_price * i.quantity).toFixed(2)}</td>
      </tr>`
    ).join('');

    const receiptHtml = `<!DOCTYPE html><html><head><meta charset="utf-8">
      <style>
        @page { margin: 0; size: 80mm auto; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Courier New', monospace; width: 80mm; padding: 4mm; font-size: 12px; color: #000; }
        .center { text-align: center; }
        .bold { font-weight: bold; }
        .divider { border-top: 1px dashed #000; margin: 6px 0; }
        .business-name { font-size: 16px; font-weight: bold; margin-bottom: 2px; }
        table { width: 100%; border-collapse: collapse; }
        .total-row { font-size: 15px; font-weight: bold; border-top: 2px solid #000; padding-top: 4px; margin-top: 4px; }
        .footer { margin-top: 10px; font-size: 10px; text-align: center; color: #555; }
      </style>
    </head><body>
      <div class="center">
        <div class="business-name">${businessName}</div>
      </div>
      <div class="divider"></div>
      <div style="display:flex;justify-content:space-between;font-size:11px">
        <span>${date}</span>
      </div>
      <div style="font-size:11px;margin-bottom:4px">Metodo: ${payMethod}</div>
      <div class="divider"></div>
      <table>${itemsHtml}</table>
      <div class="divider"></div>
      <div class="total-row" style="display:flex;justify-content:space-between">
        <span>TOTAL</span>
        <span>$${(sale.total || 0).toFixed(2)}</span>
      </div>
      <div class="divider"></div>
      <div class="footer">
        Ticket #${(sale.id || '').slice(0, 8).toUpperCase()}<br>
        Gracias por su compra
      </div>
      <script>window.onload=function(){window.print();setTimeout(function(){window.close()},500)}</script>
    </body></html>`;

    const win = window.open('', '_blank', 'width=320,height=600');
    if (win) {
      win.document.write(receiptHtml);
      win.document.close();
    } else {
      toast.error('Permite ventanas emergentes para imprimir');
    }
  };

  const handleSaveProduct = async () => {
    try {
      const { imageFile, ...formData } = productForm;
      if (imageFile) delete formData.image_url;
      let productId;
      if (editingProduct) {
        await axios.put(`${API}/pos/products/${editingProduct.id}`, formData);
        productId = editingProduct.id;
        toast.success('Producto actualizado');
      } else {
        const res = await axios.post(`${API}/pos/products`, { ...formData, gym_id: gymId });
        productId = res.data?.id;
        toast.success('Producto creado');
      }
      if (imageFile && productId) {
        await uploadProductImage(productId, imageFile);
      }
      setShowForm(false);
      setEditingProduct(null);
      setProductForm({ name: '', description: '', cost_price: 0, sale_price: 0, stock: 0, category: 'General', barcode: '', image_url: '' });
      fetchData();
    } catch (err) { toast.error(err.response?.data?.detail || 'Error'); }
  };

  const uploadProductImage = async (productId, file) => {
    setUploadingImage(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      await axios.post(`${API}/upload/product-image/${productId}`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
    } catch (err) {
      toast.error('Error al subir imagen');
    } finally { setUploadingImage(false); }
  };

  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) { toast.error('La imagen no puede superar 2MB'); return; }
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) { toast.error('Solo JPG, PNG o WEBP'); return; }
    const previewUrl = URL.createObjectURL(file);
    setProductForm(prev => ({ ...prev, imageFile: file, image_url: previewUrl }));
  };

  const handleDeleteProduct = async (id) => {
    if (!window.confirm('Eliminar producto?')) return;
    try {
      await axios.delete(`${API}/pos/products/${id}`);
      toast.success('Producto eliminado');
      fetchData();
    } catch { toast.error('Error al eliminar'); }
  };

  const handleDeleteCategory = async (cat) => {
    if (cat === 'General') { toast.error('No puedes eliminar la categoria General'); return; }
    if (!window.confirm(`Eliminar categoria "${cat}"? Los productos se moveran a "General".`)) return;
    try {
      const params = gymId ? { gym_id: gymId } : {};
      await axios.delete(`${API}/pos/categories/${encodeURIComponent(cat)}`, { params });
      toast.success('Categoria eliminada');
      setActiveCategory('all');
      fetchData();
    } catch (err) { toast.error(err.response?.data?.detail || 'Error al eliminar categoria'); }
  };

  if (loading) return <div className="flex justify-center p-12"><Loader2 className="animate-spin" size={32} /></div>;

  return (
    <div className="space-y-6" data-testid="admin-pos">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black">Punto de Venta</h1>
          <p className="text-sm text-zinc-500">{products.length} productos | {(sales || []).length} ventas</p>
        </div>
        <div className="flex items-center gap-2">
          {['pos', 'products', 'sales', 'stats'].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === tab ? 'text-black' : 'text-zinc-400 hover:text-white bg-zinc-800/50'}`}
              style={activeTab === tab ? { backgroundColor: 'var(--gym-primary)' } : {}}
              data-testid={`pos-tab-${tab}`}
            >
              {tab === 'pos' ? 'TPV' : tab === 'products' ? 'Productos' : tab === 'sales' ? 'Ventas' : 'Estadisticas'}
            </button>
          ))}
        </div>
      </div>

      {/* TAB: POS (Point of Sale) */}
      {activeTab === 'pos' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Product grid */}
          <div className="lg:col-span-2 space-y-4">
            {/* Search + Categories */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
                <Input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar producto o codigo de barras..." className="input-dark pl-10" data-testid="pos-search" />
              </div>
            </div>
            {/* Category tabs */}
            <div className="flex flex-wrap gap-2" data-testid="category-tabs">
              <button onClick={() => setActiveCategory('all')}
                className={`px-3 py-1.5 rounded-full text-xs font-bold transition-colors ${activeCategory === 'all' ? 'text-black' : 'text-zinc-400 bg-zinc-800'}`}
                style={activeCategory === 'all' ? { backgroundColor: 'var(--gym-primary)' } : {}}>
                Todos
              </button>
              {allCategories.map(cat => (
                <button key={cat} onClick={() => setActiveCategory(cat)}
                  className={`px-3 py-1.5 rounded-full text-xs font-bold transition-colors ${activeCategory.toLowerCase() === cat.toLowerCase() ? 'text-black' : 'text-zinc-400 bg-zinc-800'}`}
                  style={activeCategory.toLowerCase() === cat.toLowerCase() ? { backgroundColor: 'var(--gym-primary)' } : {}}>
                  {cat}
                </button>
              ))}
            </div>
            {/* Products grid - Touch friendly */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3" data-testid="pos-product-grid">
              {filteredProducts.map(p => (
                <motion.button key={p.id} whileTap={{ scale: 0.95 }} onClick={() => addToCart(p)}
                  className="rounded-xl text-left transition-all hover:ring-2 hover:ring-zinc-600 overflow-hidden"
                  style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-primary)' }}
                  data-testid={`pos-product-${p.id}`}
                >
                  {p.image_url ? (
                    <div className="w-full aspect-square bg-zinc-800">
                      <img src={getImageUrl(p.image_url)} alt={p.name} className="w-full h-full object-cover" />
                    </div>
                  ) : (
                    <div className="w-full aspect-square bg-zinc-800/50 flex items-center justify-center">
                      <Package size={40} className="text-zinc-600" />
                    </div>
                  )}
                  <div className="p-3">
                    <div className="flex items-start justify-between mb-1">
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-700/50 text-zinc-400">{p.category || 'General'}</span>
                      {p.stock <= 5 && <AlertTriangle size={12} className="text-amber-400" />}
                    </div>
                    <p className="font-bold text-sm truncate mt-1">{p.name}</p>
                    <p className="text-lg font-black mt-1" style={{ color: 'var(--gym-primary)' }}>${p.sale_price?.toFixed(2)}</p>
                    <p className="text-[10px] text-zinc-500">Stock: {p.stock}</p>
                  </div>
                </motion.button>
              ))}
              {filteredProducts.length === 0 && (
                <div className="col-span-full text-center py-12 text-zinc-500">
                  <Package size={32} className="mx-auto mb-2 opacity-50" />
                  <p>No hay productos</p>
                </div>
              )}
            </div>
          </div>

          {/* Cart */}
          <div className="stat-card sticky top-4 space-y-4" data-testid="pos-cart">
            <div className="flex items-center justify-between">
              <h3 className="font-bold flex items-center gap-2"><ShoppingCart size={18} /> Carrito</h3>
              {cart.length > 0 && (
                <button onClick={() => setCart([])} className="text-xs text-red-400 hover:text-red-300">Vaciar</button>
              )}
            </div>

            {cart.length === 0 ? (
              <div className="text-center py-8 text-zinc-500">
                <ShoppingCart size={32} className="mx-auto mb-2 opacity-30" />
                <p className="text-sm">Carrito vacio</p>
                <p className="text-xs">Haz clic en un producto para agregarlo</p>
              </div>
            ) : (
              <>
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {cart.map(item => (
                    <div key={item.id} className="flex items-center gap-2 p-2 rounded-lg" style={{ background: 'var(--bg-tertiary)' }}>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{item.name}</p>
                        <p className="text-xs text-zinc-500">${item.sale_price?.toFixed(2)} c/u</p>
                      </div>
                      <div className="flex items-center gap-1">
                        <button onClick={() => updateCartQty(item.id, -1)} className="w-7 h-7 rounded-lg flex items-center justify-center bg-zinc-700 hover:bg-zinc-600 text-white">
                          <Minus size={12} />
                        </button>
                        <span className="w-8 text-center text-sm font-bold">{item.qty}</span>
                        <button onClick={() => updateCartQty(item.id, 1)} className="w-7 h-7 rounded-lg flex items-center justify-center bg-zinc-700 hover:bg-zinc-600 text-white">
                          <Plus size={12} />
                        </button>
                      </div>
                      <p className="text-sm font-bold w-16 text-right">${(item.sale_price * item.qty).toFixed(2)}</p>
                    </div>
                  ))}
                </div>

                {/* Payment method */}
                <div className="pt-3 border-t border-zinc-700">
                  <p className="text-xs text-zinc-500 mb-2">Metodo de pago</p>
                  <div className="grid grid-cols-3 gap-2">
                    {[['cash', 'Efectivo'], ['card_reception', 'Tarjeta'], ['transfer', 'Transfer.']].map(([val, label]) => (
                      <button key={val} onClick={() => setPaymentMethod(val)}
                        className={`text-xs py-2 rounded-lg font-medium transition-colors ${paymentMethod === val ? 'text-black font-bold' : 'text-zinc-400 bg-zinc-800'}`}
                        style={paymentMethod === val ? { backgroundColor: 'var(--gym-primary)' } : {}}>
                        {label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Total + Pay */}
                <div className="pt-3 border-t border-zinc-700">
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-zinc-400">{cartCount} articulos</span>
                    <span className="text-2xl font-black" style={{ color: 'var(--gym-primary)' }}>${cartTotal.toFixed(2)}</span>
                  </div>
                  <Button onClick={processSale} disabled={processing} className="w-full btn-gym-primary font-bold text-base py-3" data-testid="pos-checkout-btn">
                    {processing ? <Loader2 size={18} className="animate-spin mr-2" /> : <DollarSign size={18} className="mr-2" />}
                    Cobrar ${cartTotal.toFixed(2)}
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* TAB: Products Management */}
      {activeTab === 'products' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="font-bold">Inventario de Productos</h3>
            <Button onClick={() => { setEditingProduct(null); setProductForm({ name: '', description: '', cost_price: 0, sale_price: 0, stock: 0, category: 'General', barcode: '' }); setShowForm(true); }} className="btn-gym-primary" data-testid="add-product-btn">
              <Plus size={16} className="mr-2" /> Nuevo Producto
            </Button>
          </div>

          {/* Category filter */}
          <div className="flex flex-wrap gap-2">
            <button onClick={() => setActiveCategory('all')} className={`px-3 py-1.5 rounded-full text-xs font-bold ${activeCategory === 'all' ? 'text-black' : 'text-zinc-400 bg-zinc-800'}`}
              style={activeCategory === 'all' ? { backgroundColor: 'var(--gym-primary)' } : {}}>Todos ({products.length})</button>
            {allCategories.map(cat => {
              const count = products.filter(p => (p.category || 'General') === cat).length;
              return (
                <div key={cat} className="flex items-center gap-1">
                  <button onClick={() => setActiveCategory(cat)} className={`px-3 py-1.5 rounded-full text-xs font-bold ${activeCategory.toLowerCase() === cat.toLowerCase() ? 'text-black' : 'text-zinc-400 bg-zinc-800'}`}
                    style={activeCategory.toLowerCase() === cat.toLowerCase() ? { backgroundColor: 'var(--gym-primary)' } : {}}>
                    {cat} ({count})
                  </button>
                  {cat !== 'General' && (
                    <button onClick={() => handleDeleteCategory(cat)} className="p-1 rounded-full hover:bg-red-900/30 text-red-400/60 hover:text-red-400" title="Eliminar categoria" data-testid={`delete-cat-${cat}`}>
                      <X size={12} />
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          {/* Product table */}
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead><tr><th>Producto</th><th>Categoria</th><th>Costo</th><th>Precio</th><th>Stock</th><th>Barcode</th><th>Acciones</th></tr></thead>
              <tbody>
                {filteredProducts.map(p => (
                  <tr key={p.id}>
                    <td><div><p className="font-medium">{p.name}</p>{p.description && <p className="text-xs text-zinc-500">{p.description}</p>}</div></td>
                    <td><span className="text-xs px-2 py-1 rounded-full bg-zinc-700/50 text-zinc-300">{p.category || 'General'}</span></td>
                    <td className="font-mono text-sm">${p.cost_price?.toFixed(2)}</td>
                    <td className="font-mono text-sm font-bold" style={{ color: 'var(--gym-primary)' }}>${p.sale_price?.toFixed(2)}</td>
                    <td><span className={`font-bold ${p.stock <= 5 ? 'text-amber-400' : 'text-green-400'}`}>{p.stock}</span></td>
                    <td className="text-xs font-mono text-zinc-500">{p.barcode || '-'}</td>
                    <td>
                      <div className="flex gap-1">
                        <button onClick={() => { setEditingProduct(p); setProductForm({ name: p.name, description: p.description || '', cost_price: p.cost_price || 0, sale_price: p.sale_price, stock: p.stock, category: p.category || 'General', barcode: p.barcode || '', image_url: p.image_url || '' }); setShowForm(true); }}
                          className="p-1.5 rounded hover:bg-zinc-700" data-testid={`edit-product-${p.id}`}><Edit size={14} /></button>
                        <button onClick={() => handleDeleteProduct(p.id)} className="p-1.5 rounded hover:bg-red-900/30 text-red-400" data-testid={`delete-product-${p.id}`}><Trash2 size={14} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB: Sales History */}
      {activeTab === 'sales' && (
        <div className="space-y-4">
          <h3 className="font-bold">Historial de Ventas</h3>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead><tr><th>Fecha</th><th>Articulos</th><th>Metodo</th><th className="text-right">Total</th><th></th></tr></thead>
              <tbody>
                {(sales || []).map(s => (
                  <tr key={s.id}>
                    <td className="text-sm">{s.created_at ? new Date(s.created_at).toLocaleString() : '-'}</td>
                    <td><div className="flex flex-wrap gap-1">{(s.items || []).map((i, idx) => (
                      <span key={idx} className="text-xs bg-zinc-800 px-2 py-0.5 rounded">{i.quantity}x {i.product_name || i.product_id?.slice(0,8)}</span>
                    ))}</div></td>
                    <td><span className={`badge ${s.payment_method === 'cash' ? 'badge-success' : 'badge-primary'}`}>
                      {s.payment_method === 'cash' ? 'Efectivo' : s.payment_method === 'card_reception' ? 'Tarjeta' : 'Transfer.'}
                    </span></td>
                    <td className="text-right font-mono font-bold">${s.total?.toFixed(2)}</td>
                    <td>
                      <button onClick={() => printReceipt(s)} className="p-1.5 rounded hover:bg-zinc-700 text-zinc-400 hover:text-white" title="Imprimir ticket" data-testid={`print-sale-${s.id}`}>
                        <Printer size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
                {(sales || []).length === 0 && <tr><td colSpan={4} className="text-center text-zinc-500">No hay ventas</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB: Stats */}
      {activeTab === 'stats' && stats && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="stat-card"><p className="text-xs text-zinc-500">Ventas Hoy</p><p className="text-2xl font-black" style={{ color: 'var(--gym-primary)' }}>${stats.today_total?.toFixed(2) || '0'}</p></div>
            <div className="stat-card"><p className="text-xs text-zinc-500">Ventas Mes</p><p className="text-2xl font-black">${stats.month_total?.toFixed(2) || '0'}</p></div>
            <div className="stat-card"><p className="text-xs text-zinc-500">Productos</p><p className="text-2xl font-black">{stats.total_products || 0}</p></div>
            <div className="stat-card"><p className="text-xs text-zinc-500">Stock Bajo</p><p className="text-2xl font-black text-amber-400">{(stats.low_stock_products || []).length}</p></div>
          </div>
          {(stats.low_stock_products || []).length > 0 && (
            <div className="stat-card">
              <h4 className="font-bold text-amber-400 flex items-center gap-2 mb-3"><AlertTriangle size={16} /> Productos con Stock Bajo</h4>
              <div className="space-y-2">
                {stats.low_stock_products.map(p => (
                  <div key={p.id} className="flex justify-between items-center p-2 rounded-lg bg-amber-500/5">
                    <span className="text-sm">{p.name}</span>
                    <span className="font-bold text-amber-400">{p.stock} uds.</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Product Form Dialog */}
      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="dialog-content max-w-md max-h-[90vh] overflow-y-auto">
          <DialogHeader><DialogTitle>{editingProduct ? 'Editar Producto' : 'Nuevo Producto'}</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-zinc-400">Nombre *</label>
              <Input value={productForm.name} onChange={e => setProductForm({...productForm, name: e.target.value})} className="input-dark" data-testid="product-name-input" />
            </div>
            <div>
              <label className="text-sm text-zinc-400">Descripcion</label>
              <Input value={productForm.description} onChange={e => setProductForm({...productForm, description: e.target.value})} className="input-dark" />
            </div>
            <div>
              <label className="text-sm text-zinc-400">Categoria</label>
              <div className="flex gap-2">
                <select value={productForm.category} onChange={e => setProductForm({...productForm, category: e.target.value})} className="input-dark flex-1 rounded-lg px-3 py-2" data-testid="product-category-select">
                  {DEFAULT_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                  {allCategories.filter(c => !DEFAULT_CATEGORIES.includes(c)).map(c => <option key={c} value={c}>{c}</option>)}
                </select>
                <Button variant="outline" className="border-zinc-700" onClick={() => {
                  const newCat = prompt('Nueva categoria:');
                  if (newCat) setProductForm({...productForm, category: newCat});
                }}>+</Button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="text-sm text-zinc-400">Precio Costo</label>
                <Input type="number" step="0.01" value={productForm.cost_price} onChange={e => setProductForm({...productForm, cost_price: parseFloat(e.target.value) || 0})} className="input-dark" /></div>
              <div><label className="text-sm text-zinc-400">Precio Venta *</label>
                <Input type="number" step="0.01" value={productForm.sale_price} onChange={e => setProductForm({...productForm, sale_price: parseFloat(e.target.value) || 0})} className="input-dark" data-testid="product-price-input" /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="text-sm text-zinc-400">Stock</label>
                <Input type="number" value={productForm.stock} onChange={e => setProductForm({...productForm, stock: parseInt(e.target.value) || 0})} className="input-dark" data-testid="product-stock-input" /></div>
              <div><label className="text-sm text-zinc-400">Codigo de Barras</label>
                <Input value={productForm.barcode} onChange={e => setProductForm({...productForm, barcode: e.target.value})} className="input-dark" placeholder="Opcional" /></div>
            </div>
            <div>
              <label className="text-sm text-zinc-400">Imagen del Producto</label>
              <input type="file" ref={fileInputRef} accept="image/jpeg,image/png,image/webp" onChange={handleImageSelect} className="hidden" />
              <div className="mt-2 flex items-center gap-3">
                {(productForm.image_url && !productForm.imageFile) ? (
                  <div className="relative w-24 h-24 rounded-xl overflow-hidden bg-zinc-800 group">
                    <img src={getImageUrl(productForm.image_url)} alt="Preview" className="w-full h-full object-cover" />
                    <button type="button" onClick={() => { setProductForm(prev => ({ ...prev, image_url: '', imageFile: null })); }}
                      className="absolute top-1 right-1 p-1 bg-black/60 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                      <X size={12} className="text-white" />
                    </button>
                  </div>
                ) : productForm.imageFile ? (
                  <div className="relative w-24 h-24 rounded-xl overflow-hidden bg-zinc-800 group">
                    <img src={productForm.image_url} alt="Preview" className="w-full h-full object-cover" />
                    <button type="button" onClick={() => { setProductForm(prev => ({ ...prev, image_url: '', imageFile: null })); }}
                      className="absolute top-1 right-1 p-1 bg-black/60 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                      <X size={12} className="text-white" />
                    </button>
                  </div>
                ) : (
                  <div className="w-24 h-24 rounded-xl bg-zinc-800 flex items-center justify-center border-2 border-dashed border-zinc-600">
                    <ImageIcon size={24} className="text-zinc-600" />
                  </div>
                )}
                <Button type="button" variant="outline" onClick={() => fileInputRef.current?.click()}
                  className="border-zinc-700 text-zinc-300 hover:bg-zinc-800" data-testid="product-upload-image-btn">
                  <Camera size={16} className="mr-2" /> {productForm.image_url ? 'Cambiar' : 'Subir Foto'}
                </Button>
              </div>
              <p className="text-[10px] text-zinc-500 mt-1">JPG, PNG o WEBP. Maximo 2MB</p>
            </div>
            {productForm.cost_price > 0 && productForm.sale_price > 0 && (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                <p className="text-xs text-emerald-400">Margen: ${(productForm.sale_price - productForm.cost_price).toFixed(2)} ({((productForm.sale_price - productForm.cost_price) / productForm.cost_price * 100).toFixed(0)}%)</p>
              </div>
            )}
            <Button onClick={handleSaveProduct} className="w-full btn-gym-primary" disabled={!productForm.name || !productForm.sale_price} data-testid="save-product-btn">
              <Save size={16} className="mr-2" /> {editingProduct ? 'Actualizar' : 'Crear Producto'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
