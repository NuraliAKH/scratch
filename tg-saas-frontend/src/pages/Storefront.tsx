import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { ShoppingCart, Globe } from 'lucide-react';
import { useParams } from 'react-router-dom';

export default function Storefront() {
  const { storeId } = useParams();
  const { t, i18n } = useTranslation();
  const [lang, setLang] = useState(i18n.language);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // В будущем здесь будет реальный API вызов: fetch(`http://localhost:3000/products/${storeId}`)
    setTimeout(() => {
      setProducts([
        { id: '1', title: 'Product 1', price: 10.00 },
        { id: '2', title: 'Product 2', price: 15.50 },
        { id: '3', title: 'Product 3', price: 5.99 },
      ]);
      setLoading(false);
    }, 1000);
  }, [storeId]);

  const changeLanguage = () => {
    const nextLang = lang === 'ru' ? 'uz' : lang === 'uz' ? 'en' : 'ru';
    i18n.changeLanguage(nextLang);
    setLang(nextLang);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-20">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 py-3 flex justify-between items-center">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Store {storeId}
          </h1>
          <div className="flex items-center gap-4">
            <button 
              onClick={changeLanguage}
              className="flex items-center gap-1 text-sm font-medium text-slate-600 bg-slate-100 px-2 py-1 rounded-md active:scale-95 transition-transform"
            >
              <Globe size={16} />
              {lang.toUpperCase()}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-md mx-auto px-4 py-6">
        <div className="bg-indigo-100 rounded-xl p-6 mb-6 text-center shadow-inner">
          <h2 className="text-2xl font-bold text-indigo-900 mb-2">{t('welcome')}!</h2>
          <p className="text-indigo-700 text-sm">Find the best products right here.</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {loading ? (
            [1, 2, 3, 4].map((item) => (
              <div key={item} className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                <div className="h-32 bg-slate-200 w-full animate-pulse"></div>
                <div className="p-3">
                  <div className="h-4 bg-slate-200 rounded w-3/4 mb-2 animate-pulse"></div>
                  <div className="h-4 bg-slate-200 rounded w-1/4 animate-pulse"></div>
                </div>
              </div>
            ))
          ) : (
            products.map((product) => (
              <div key={product.id} className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden active:scale-[0.98] transition-transform cursor-pointer">
                <div className="h-32 bg-slate-100 flex items-center justify-center text-slate-400">
                  No Image
                </div>
                <div className="p-3">
                  <h3 className="font-semibold text-sm mb-1 truncate">{product.title}</h3>
                  <p className="text-blue-600 font-bold">${product.price.toFixed(2)}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </main>

      {/* Floating Cart */}
      <div className="fixed bottom-4 left-0 right-0 max-w-md mx-auto px-4">
        <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-xl shadow-lg flex justify-between items-center active:scale-[0.98] transition-transform">
          <div className="flex items-center gap-2">
            <ShoppingCart size={20} />
            <span>{t('cart')}</span>
          </div>
          <span className="bg-blue-700 px-2 py-1 rounded-md text-sm">0 items</span>
        </button>
      </div>
    </div>
  );
}
