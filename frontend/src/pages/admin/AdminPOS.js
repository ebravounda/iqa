import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getPOSProducts, createPOSProduct, updatePOSProduct, deletePOSProduct, createPOSSale, getPOSSales, getPOSStats, getGymSaaSFeatures, getGyms, uploadProductImage } from '../../lib/api';
import { toast } from 'sonner';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Camera, ImageIcon } from 'lucide-react';

const CURRENCY_SYMBOLS = { EUR: '\u20ac', USD: '$', CLP: '$', ARS: '$' };

export default function AdminPOS() {
  const { admin, isSuperAdmin } = useAuth();
  const [selectedGym, setSelectedGym] = useState(admin?.gym_id || '');
  const [gymsList, setGymsList] = useState([]);
  const gymId = isSuperAdmin ? selectedGym : admin?.gym_id;
  const [tab, setTab] = useState('sell');
  const [products, setProducts] = useState([]);
  const [sales, setSales] = useState([]);
  const [stats, setStats] = useState(null);
  const [cart, setCart] = useState([]);
  const [showProductForm, setShowProductForm] = useState(false);
  const [hasAccess, setHasAccess] = useState(null);
  const [currency, setCurrency] = useState('EUR');
  const [productForm, setProductForm] = useState({ gym_id: gymId || '', name: '', description: '', cost_price: 0, sale_price: 0, stock: 0, category: '', barcode: '' });
  const [paymentMethod, setPaymentMethod] = useState('cash');

  useEffect(() => {
    if (isSuperAdmin) {
      getGyms().then(res => {
        setGymsList(res.data);
        if (res.data.length > 0 && !selectedGym) setSelectedGym(res.data[0].id);
      }).catch(() => {});
    }
  }, [isSuperAdmin]);

  const cs = CURRENCY_SYMBOLS[currency] || '$';

  const load = useCallback(async () => {
    if (!gymId) return;
    try {
      if (gymId) {
        const feat = await getGymSaaSFeatures(gymId);
        if (!feat.data.has_pos) { setHasAccess(false); return; }
      }
      setHasAccess(true);
      const [p, s, st] = await Promise.all([getPOSProducts(gymId), getPOSSales(gymId), getPOSStats(gymId)]);
      setProducts(p.data);
      setSales(s.data);
      setStats(st.data);
      if (s.data.length > 0 && s.data[0].currency) setCurrency(s.data[0].currency);
    } catch (e) { 
      console.error('TPV Error:', e?.response?.status, e?.response?.data, e?.message);
      toast.error(`Error TPV: ${e?.response?.data?.detail || e?.message || 'Error de conexion'}`); 
    }
  }, [gymId, admin]);

  useEffect(() => { if (gymId) load(); }, [load, gymId]);

  if (!gymId && isSuperAdmin) return (
    <div className="space-y-6" data-testid="pos-page">
      <div><h1 className="text-2xl font-black text-white">TPV / Punto de Venta</h1></div>
      <div className="max-w-sm">
        <label className="text-sm text-zinc-400 mb-1 block">Seleccionar Gimnasio</label>
        <Select value={selectedGym} onValueChange={setSelectedGym}>
          <SelectTrigger className="bg-zinc-900 border-zinc-700" data-testid="pos-gym-select">
            <SelectValue placeholder="Seleccionar gimnasio" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-900 border-zinc-700">
            {gymsList.map(g => <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
    </div>
  );

  if (hasAccess === false) return (
    <div className="p-8 text-center" data-testid="pos-no-access">
      <h2 className="text-xl font-bold text-white mb-2">TPV no disponible</h2>
      <p className="text-zinc-400">El plan SaaS de este gimnasio no incluye el modulo TPV/POS. Contacta al administrador para actualizar tu plan.</p>
    </div>
  );

  const addToCart = (product) => {
    const existing = cart.find(c => c.product_id === product.id);
    if (existing) {
      if (existing.quantity >= product.stock) { toast.error('Stock insuficiente'); return; }
      setCart(cart.map(c => c.product_id === product.id ? { ...c, quantity: c.quantity + 1 } : c));
    } else {
      if (product.stock <= 0) { toast.error('Sin stock'); return; }
      setCart([...cart, { product_id: product.id, product_name: product.name, quantity: 1, unit_price: product.sale_price }]);
    }
  };

  const cartTotal = cart.reduce((sum, item) => sum + item.quantity * item.unit_price, 0);

  const processSale = async () => {
    if (cart.length === 0) { toast.error('Agrega productos al carrito'); return; }
    try {
      const saleData = {
        gym_id: gymId || products[0]?.gym_id,
        items: cart.map(c => ({ product_id: c.product_id, quantity: c.quantity, unit_price: c.unit_price })),
        payment_method: paymentMethod,
      };
      await createPOSSale(saleData);
      toast.success('Venta registrada');
      setCart([]);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Error en venta'); }
  };

  const handleCreateProduct = async (e) => {
    e.preventDefault();
    try {
      const data = { ...productForm, gym_id: gymId || productForm.gym_id };
      await createPOSProduct(data);
      toast.success('Producto creado');
      setShowProductForm(false);
      setProductForm({ gym_id: gymId || '', name: '', description: '', cost_price: 0, sale_price: 0, stock: 0, category: '', barcode: '' });
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Error'); }
  };

  const handleProductImageUpload = async (productId, file) => {
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) { toast.error('La imagen no puede superar 2MB'); return; }
    try {
      await uploadProductImage(productId, file);
      toast.success('Imagen del producto actualizada');
      load();
    } catch (err) { toast.error(err.response?.data?.detail || 'Error al subir imagen'); }
  };

  const getProductImageUrl = (product) => {
    if (!product.image_path) return null;
    return `${process.env.REACT_APP_BACKEND_URL}/api/files/${product.image_path}`;
  };

  const printReceipt = (sale) => {
    const w = window.open('', '_blank', 'width=302,height=600');
    const items = (sale.items || []).map(i => `<tr><td style="font-size:11px">${i.product_name}</td><td style="text-align:right;font-size:11px">${i.quantity}x${cs}${i.unit_price}</td></tr>`).join('');
    w.document.write(`<html><head><style>body{font-family:monospace;width:72mm;margin:0 auto;padding:4mm;}table{width:100%}td{padding:2px 0}hr{border:0;border-top:1px dashed #000;margin:8px 0}</style></head><body>
      <h3 style="text-align:center;margin:4px 0">TICKET DE VENTA</h3>
      <p style="text-align:center;font-size:10px">${new Date(sale.created_at).toLocaleString()}</p><hr/>
      <table>${items}</table><hr/>
      <p style="text-align:right;font-weight:bold">TOTAL: ${cs}${sale.total?.toLocaleString()}</p>
      <p style="font-size:10px">Pago: ${sale.payment_method === 'cash' ? 'Efectivo' : sale.payment_method === 'card' ? 'Tarjeta' : sale.payment_method}</p>
      <p style="text-align:center;font-size:9px;margin-top:12px">Gracias por su compra</p>
    </body></html>`);
    w.document.close();
    w.print();
  };

  return (
    <div className="space-y-6" data-testid="pos-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white">TPV / Punto de Venta</h1>
          <p className="text-zinc-400 text-sm">Ventas, inventario y tickets</p>
        </div>
        {isSuperAdmin && (
          <div className="min-w-[200px]">
            <Select value={selectedGym} onValueChange={setSelectedGym}>
              <SelectTrigger className="bg-zinc-900 border-zinc-700" data-testid="pos-gym-select">
                <SelectValue placeholder="Gimnasio" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-zinc-700">
                {gymsList.map(g => <SelectItem key={g.id} value={g.id}>{g.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4"><p className="text-zinc-400 text-xs">Ventas hoy</p><p className="text-xl font-bold text-white">{stats.today_sales}</p></div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4"><p className="text-zinc-400 text-xs">Ingresos hoy</p><p className="text-xl font-bold text-[var(--gym-primary)]">{cs}{stats.today_revenue?.toLocaleString()}</p></div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4"><p className="text-zinc-400 text-xs">Ventas mes</p><p className="text-xl font-bold text-white">{stats.month_sales}</p></div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4"><p className="text-zinc-400 text-xs">Ingresos mes</p><p className="text-xl font-bold text-[var(--gym-primary)]">{cs}{stats.month_revenue?.toLocaleString()}</p></div>
        </div>
      )}

      <div className="flex gap-2">
        {['sell', 'products', 'history'].map(t => (
          <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${tab === t ? 'bg-[var(--gym-primary)] text-black' : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'}`} data-testid={`pos-tab-${t}`}>
            {t === 'sell' ? 'Vender' : t === 'products' ? 'Productos' : 'Historial'}
          </button>
        ))}
      </div>

      {tab === 'sell' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 grid grid-cols-2 sm:grid-cols-3 gap-3">
            {products.map(p => (
              <button key={p.id} onClick={() => addToCart(p)} className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden text-left hover:border-[var(--gym-primary)] transition-colors" data-testid={`pos-product-${p.id}`} disabled={p.stock <= 0}>
                {getProductImageUrl(p) ? (
                  <div className="w-full h-28 bg-zinc-800">
                    <img src={getProductImageUrl(p)} alt={p.name} className="w-full h-full object-cover" />
                  </div>
                ) : (
                  <div className="w-full h-28 bg-zinc-800/50 flex items-center justify-center">
                    <ImageIcon size={32} className="text-zinc-700" />
                  </div>
                )}
                <div className="p-3">
                  <p className="text-white font-semibold truncate text-sm">{p.name}</p>
                  <p className="text-[var(--gym-primary)] font-bold">{cs}{p.sale_price?.toLocaleString()}</p>
                  <p className={`text-xs ${p.stock <= 5 ? 'text-red-400' : 'text-zinc-400'}`}>Stock: {p.stock}</p>
                </div>
              </button>
            ))}
            {products.length === 0 && <p className="text-zinc-500 col-span-full text-center py-8">No hay productos. Crea algunos en la pestana "Productos".</p>}
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5" data-testid="pos-cart">
            <h3 className="font-bold text-white mb-3">Carrito</h3>
            {cart.length === 0 ? <p className="text-zinc-500 text-sm">Vacio</p> : (
              <div className="space-y-2 mb-4">
                {cart.map((item, i) => (
                  <div key={i} className="flex items-center justify-between bg-zinc-800 rounded-lg p-2">
                    <div>
                      <p className="text-white text-sm">{item.product_name}</p>
                      <p className="text-zinc-400 text-xs">{item.quantity}x {cs}{item.unit_price?.toLocaleString()}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button onClick={() => setCart(cart.map(c => c.product_id === item.product_id ? { ...c, quantity: Math.max(1, c.quantity - 1) } : c))} className="w-6 h-6 bg-zinc-700 rounded text-white text-xs">-</button>
                      <span className="text-white text-sm w-4 text-center">{item.quantity}</span>
                      <button onClick={() => addToCart({ id: item.product_id, name: item.product_name, sale_price: item.unit_price, stock: 999 })} className="w-6 h-6 bg-zinc-700 rounded text-white text-xs">+</button>
                      <button onClick={() => setCart(cart.filter(c => c.product_id !== item.product_id))} className="w-6 h-6 bg-red-900/30 rounded text-red-400 text-xs ml-1">x</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="border-t border-zinc-700 pt-3 mb-3">
              <p className="text-lg font-bold text-white">Total: <span className="text-[var(--gym-primary)]">{cs}{cartTotal.toLocaleString()}</span></p>
            </div>
            <div className="flex gap-2 mb-3">
              {['cash', 'card'].map(m => (
                <button key={m} onClick={() => setPaymentMethod(m)} className={`flex-1 py-2 rounded-lg text-sm font-semibold ${paymentMethod === m ? 'bg-[var(--gym-primary)] text-black' : 'bg-zinc-800 text-zinc-300'}`} data-testid={`pos-payment-${m}`}>
                  {m === 'cash' ? 'Efectivo' : 'Tarjeta'}
                </button>
              ))}
            </div>
            <button onClick={processSale} disabled={cart.length === 0} className="w-full btn-gym-primary disabled:opacity-50" data-testid="pos-complete-sale">
              Completar Venta
            </button>
          </div>
        </div>
      )}

      {tab === 'products' && (
        <div>
          <div className="flex justify-end mb-4">
            <button onClick={() => setShowProductForm(!showProductForm)} className="btn-gym-primary text-sm" data-testid="add-product-btn">+ Nuevo Producto</button>
          </div>
          {showProductForm && (
            <form onSubmit={handleCreateProduct} className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 mb-4 grid grid-cols-1 md:grid-cols-3 gap-3" data-testid="product-form">
              <div>
                <label className="text-xs text-zinc-400 block mb-1">Nombre del producto *</label>
                <input className="input-gym" placeholder="Ej: Batido proteina" value={productForm.name} onChange={e => setProductForm({ ...productForm, name: e.target.value })} required />
              </div>
              <div>
                <label className="text-xs text-zinc-400 block mb-1">Precio de costo</label>
                <input className="input-gym" type="number" step="0.01" placeholder="0.00" value={productForm.cost_price} onChange={e => setProductForm({ ...productForm, cost_price: parseFloat(e.target.value) || 0 })} />
              </div>
              <div>
                <label className="text-xs text-zinc-400 block mb-1">Precio de venta *</label>
                <input className="input-gym" type="number" step="0.01" placeholder="0.00" value={productForm.sale_price} onChange={e => setProductForm({ ...productForm, sale_price: parseFloat(e.target.value) || 0 })} required />
              </div>
              <div>
                <label className="text-xs text-zinc-400 block mb-1">Stock inicial</label>
                <input className="input-gym" type="number" placeholder="0" value={productForm.stock} onChange={e => setProductForm({ ...productForm, stock: parseInt(e.target.value) || 0 })} />
              </div>
              <div>
                <label className="text-xs text-zinc-400 block mb-1">Categoria</label>
                <input className="input-gym" placeholder="Ej: Bebidas, Suplementos" value={productForm.category} onChange={e => setProductForm({ ...productForm, category: e.target.value })} />
              </div>
              <div>
                <label className="text-xs text-zinc-400 block mb-1">Codigo de barras</label>
                <input className="input-gym" placeholder="Opcional" value={productForm.barcode} onChange={e => setProductForm({ ...productForm, barcode: e.target.value })} />
              </div>
              <div className="col-span-full flex gap-3">
                <button type="submit" className="btn-gym-primary" data-testid="save-product-btn">Guardar Producto</button>
                <button type="button" onClick={() => setShowProductForm(false)} className="btn-gym-secondary">Cancelar</button>
              </div>
            </form>
          )}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-zinc-800"><th className="text-left p-3 text-zinc-400 font-medium w-12">Img</th><th className="text-left p-3 text-zinc-400 font-medium">Producto</th><th className="text-right p-3 text-zinc-400">Costo</th><th className="text-right p-3 text-zinc-400">Venta</th><th className="text-right p-3 text-zinc-400">Stock</th><th className="text-right p-3 text-zinc-400">Acciones</th></tr></thead>
              <tbody>
                {products.map(p => (
                  <tr key={p.id} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                    <td className="p-2">
                      {getProductImageUrl(p) ? (
                        <img src={getProductImageUrl(p)} alt={p.name} className="w-10 h-10 rounded-lg object-cover" />
                      ) : (
                        <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center">
                          <ImageIcon size={16} className="text-zinc-600" />
                        </div>
                      )}
                    </td>
                    <td className="p-3 text-white">{p.name}<span className="text-zinc-500 text-xs ml-2">{p.category}</span></td>
                    <td className="p-3 text-right text-zinc-400">{cs}{p.cost_price?.toLocaleString()}</td>
                    <td className="p-3 text-right text-[var(--gym-primary)] font-semibold">{cs}{p.sale_price?.toLocaleString()}</td>
                    <td className={`p-3 text-right font-mono ${p.stock <= 5 ? 'text-red-400' : 'text-zinc-300'}`}>{p.stock}</td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <label className="cursor-pointer text-violet-400 hover:text-violet-300 text-xs flex items-center gap-1" data-testid={`product-upload-img-${p.id}`}>
                          <Camera size={14} /> Foto
                          <input type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={(e) => handleProductImageUpload(p.id, e.target.files[0])} />
                        </label>
                        <button onClick={() => deletePOSProduct(p.id).then(load)} className="text-red-400 text-xs hover:underline">Eliminar</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {products.length === 0 && <p className="text-zinc-500 text-center py-6">Sin productos</p>}
          </div>
        </div>
      )}

      {tab === 'history' && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden" data-testid="pos-history">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-zinc-800"><th className="text-left p-3 text-zinc-400">Fecha</th><th className="text-left p-3 text-zinc-400">Items</th><th className="text-right p-3 text-zinc-400">Total</th><th className="text-center p-3 text-zinc-400">Pago</th><th className="text-center p-3 text-zinc-400">Ticket</th></tr></thead>
            <tbody>
              {sales.map(s => (
                <tr key={s.id} className="border-b border-zinc-800/50 hover:bg-zinc-800/30">
                  <td className="p-3 text-zinc-300">{new Date(s.created_at).toLocaleString()}</td>
                  <td className="p-3 text-white">{(s.items || []).map(i => `${i.product_name}(${i.quantity})`).join(', ')}</td>
                  <td className="p-3 text-right text-[var(--gym-primary)] font-bold">{cs}{s.total?.toLocaleString()}</td>
                  <td className="p-3 text-center"><span className={`text-xs px-2 py-1 rounded ${s.payment_method === 'cash' ? 'bg-green-900/30 text-green-400' : 'bg-blue-900/30 text-blue-400'}`}>{s.payment_method === 'cash' ? 'Efectivo' : 'Tarjeta'}</span></td>
                  <td className="p-3 text-center"><button onClick={() => printReceipt(s)} className="text-xs text-[var(--gym-primary)] hover:underline" data-testid={`print-receipt-${s.id}`}>Imprimir</button></td>
                </tr>
              ))}
            </tbody>
          </table>
          {sales.length === 0 && <p className="text-zinc-500 text-center py-6">Sin ventas</p>}
        </div>
      )}

      {stats?.low_stock_products?.length > 0 && (
        <div className="bg-red-900/20 border border-red-900/40 rounded-xl p-4" data-testid="low-stock-alert">
          <h4 className="text-red-400 font-semibold text-sm mb-2">Stock bajo</h4>
          <div className="flex flex-wrap gap-2">
            {stats.low_stock_products.map(p => (
              <span key={p.id} className="text-xs bg-red-900/30 text-red-300 px-2 py-1 rounded">{p.name}: {p.stock} uds</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
