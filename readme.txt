app.sgnIPC API:

взаимодействие править в фяйле /services/gui/gui.py - этот объект SgnGUI педедается в app.sgnIPC
подписываться на события надо именно в этом фяйле и дальше передавать в QT


Объект app.sgnIPC представляет собой разделяемый массив, а также набор разделяемых методов.
Разделяемые методы обьявляются через @subscribe - подписка на событие с аргументами
Например:
файл gui.py:
class SgnGUI(sgnService):
	@subscribe
	def EventMoneyStacked(self,amount,mtype):
		self.info('Пополение баланса на %s через %s'%(self.nominal_to_text_with_currency(amount),mtype))		
файл payment.py:
class SgnPayment(sgnService):
	...
	self.EventMoneyStacked(100,'CASH')
	...
Описание:
self.EventMoneyStacked(100,'CASH') - Произведет вызов внутри всех файлов где есть @subscribe EventMoneyStacked вне зависимости внутри какого процесса он зарегистрирован
Возвращаемое значение: tuple всех результатов вызываемыч методов

Значения разделяемого массива:
Пример:
файл session.py:
class SgnSession(sgnService):
	def __init__(self):
		super().__init__()
		self.session_init()

	def session_init(self):
		self['session']=dict(
			session_type=False,
			cash_balance=0,
			escrow_balance=0,
			e_balance=0,
			client_balance=0,
			liter_balance=0,
			is_dispensing=False,
			query_amount=False,
			complete=False,
			)
после этого станет доступным обращение из любого файла:
self['session']['cash_balance'] и т.п.



Система логирования:

Весь вывод программы, осуществляемый вне данных методов может быть потерян и не сохранен в логах!!!

app.sgnIPC.debug(text)
вывод отладочного сообщения (отключаются в продакшен)
app.sgnIPC.info(text)
вывод информационного сообщения (стандартные сообщения в лог)
app.sgnIPC.warning(text)
вывод предупреюдения (ошибка, неисправность или событне не привидящее к невозмоюножти выполтить действие)
app.sgnIPC.error(text)
вывод ошибки (проблема приводящая к невозмоюности выполнения действия)
app.sgnIPC.critical(text)
критическая ошибка (проблема или неисправность привидящая к невозмоюности работы системы или контроль ошибки в программе)
app.sgnIPC.exception(text_or_exception_obj)
Исключение - обычное исключение - аргумент может быть как текстом так и объектом типа Exception
try:
	...
except Exception as e:
	app.sgnIPC.exception(e)


Сессия:
app.sgnIPC['session']['session_type'] - тип сессии (CASH/CASHLESS/...)
app.sgnIPC['session']['cash_balance'] - баланс за наличные (без учета наличных в полоюении ESCROW)
app.sgnIPC['session']['escrow_balance'] - баланс за наличные, находящиеся в ESCROW
app.sgnIPC['session']['e_balance'] - баланс за безналичные
app.sgnIPC['session']['client_balance'] - баланс на карте клиента
app.sgnIPC['session']['liter_balance'] - литровый баланс
app.sgnIPC['session']['is_dispensing'] - выдается сдача
app.sgnIPC['session']['query_amount'] - сумма требуемая для внесения, False - неизвестна (без ограничений)
	как только внесенные денеюные средства станут равны или больше чем 'query_amount' устройства приема денежных средств автоматически отключатся и придет событие EventPaymentComplete
	такюе параметр влияет на помещение купюры на удержание - помещается купюра которая вызвала событие EventPaymentComplete
app.sgnIPC['session']['complete'] - сессия завершена

app.sgnIPC.StartSession(session_type) - начать сессию, session_type - тип сессии (CASH/CASHLESS/...)
	после начала сессии можно установить app.sgnIPC['session']['query_amount']
app.sgnIPC.ChangeSession(session_type) - изменить сессию, session_type - тип сессии (CASH/CASHLESS/...)
app.sgnIPC.EndSession() - завершить сессию, произойдет возврат купюры в ESCROW и выдача сдачи или возврат неиспользованных денежных средств по банковской карте


Управление устрйствами приема:
app.sgnIPC.DeactivateAllPayments() - отключить прием всех видов приема денежных средств
app.sgnIPC.ActivateCash() - включить прием наличных
События:
@subscribe
def EventBalanceChanged(self) - изменился баланс
@subscribe
def EventMoneyStacked(self,amount,mtype) - принята купюра/монета и т.п. amount-сумма, mtype-тип (CASH/CASHLESS/...)
@subscribe
def EventPayoutStarted(self,group,name,amount) - начинается выдача сдачи
@subscribe
def EventPayoutProgress(self,group,name,amount) - выдалась часть сдачи
@subscribe
def EventPayoutFinished(self,group,name,amount,required) - выдача сдачи завершена
		amount - выданная сумма
		required - сумма которая должна была выдана
		если они не совпадают то возможно не хватает номиналов или неисправность
@subscribe
def EventPaymentComplete(self) - прием денежных средств завершен - только если app.sgnIPC['session']['query_amount'] не False
@subscribe
def EventPaymentEscrowLever(self,group,name,message) - нажата кнопка возврата монет
@subscribe
def EventPaymentError(self,group,name,code,message) - ошибка устройства
@subscribe
def EventPaymentFault(self,group,name,code,message) - неисправность/отказ устройства, не удалось активировать
@subscribe
def EventPaymentReady(self,group,name) - устройство готово к приему
@subscribe
def EventMoneyRejected(self,amount,mtype) - возврат номинала
@subscribe
def EventNominalIsHigh(self,group,name,nominal,route_txt,is_bill,payout_amount_after) - Останется мало сдачи или не хватит вообще тк купюра слишком велика. Купюра помещается на ESCROW. Нужно спросить клиента что делать. По решению клиента вызвать app.sgnIPC.AcceptEscrow() или app.sgnIPC.RejectEscrow()

Продажа:
1. Вызвать app.sgnIPC.DepositAmount(amount) - где amount сумма в копейках, которую предполагается списать
2. Дождаться события app.sgnIPC.DepositNCK(reason) - отказ или app.sgnIPC.DepositACK() - одобрено
3. Если одобрено, то налить/выдать товар
4. Вызвать app.sgnIPC.AcknowlegeAmount(amount) - где amount сумма в копейках фактически потраченная клиентом (не должна превышать сумму, указанную в п.1 DepositAmount(amount))

Состояния устройств приема:
app.sgnIPC['accept']=dict(
			coin=False,	 - принимаем ли монеты
			bill=False,  - принимаем ли купюры
			client_card=False, - принимаем ли карты клиента
			bank_card=False, - принимаем ли карты банка
			sbp=False,  - принимаем ли sbp
			qr_reader=False, - принимаем ли qr-коды
			)
app.sgnIPC['dispense']=dict( - аналогично что можен выдавать
	coin=False,
	bill=False,
	bank_full=False,
	bank_partial=False,
	sbp=False,
	)
app.sgnIPC['dispense_amount']=dict( - суммы которые можем выдавать
	coin=0,
	bill=0,
	)
app.sgnIPC['disabled_nominals']=dict( - списки монет и купюр заперщенных к приему
	coin=[],
	bill=[]
	)
app.sgnIPC['currency']='RUR' - валюта
app.sgnIPC['currency_decimals'] - сколько знаков у копеек
app.sgnIPC['payment_method'] - описание методов оплаты:
app.sgnIPC['payment_method']['CASH'] - наличные
app.sgnIPC['payment_method']['CASHLESS'] - безнал
	внури данных структур находятся описания устройств, может содержать специфичные для данного устройства поля
	['can_be_used'] - может использоваться
	['is_ready'] - готов
	['is_enabled'] - разрешен
	['status'] - состояние
	['setup'] - параметы
	['ident'] - идентификация
пример использования:
	def can_accept_coins(self):
		return self['accept']['coin']

	def can_accept_bills(self):
		return self['accept']['bill']

	def can_dispense_coins(self):
		return self['dispense']['coin'] and (self['dispense_amount']['coin']>=self.min_coin_dispense_amount)

	def can_dispense_bills(self):
		return self['dispense']['bill'] and (self['dispense_amount']['bill']>=self.min_bill_dispense_amount)

	def can_accept_cash(self):
		return self.can_accept_coins() or self.can_accept_bills()

	def can_dispense_cash(self):
		return self.can_dispense_coins() or self.can_dispense_bills()


Пример сессии:
	l=app.sgnIPC
	#отключить прием денег
	l.DeactivateAllPayments()
	#Начать сессию за нал
	l.StartSession('CASH')
	#Установить сумму в 150р (указывается в копейках см. app.sgnIPC['currency_decimals'])
	l['session']['query_amount']=15000
	try:
		try:
			while True:
				#Ждем когда появятся устройства для приема
				if l.can_accept_cash():
					#На всякий случай подеждем еще - вдруг еще не все устройства обнаружены - толко в тестовых целях
					time.sleep(5)				
					#Активируем устройства приема
					l.ActivateCash()
					#Тут надо подождать EventPaymentReady, EventPaymentFault, EventPaymentError по каждому устройству
					#А то вдруг ничего не активировалось
					#Ждем 1 минуту для того чтобы внести наличные
					#Тут правильнее ждать EventPaymentComplete тк мы задали l['session']['query_amount']
					time.sleep(60)
					break
				else:
					#задержка чтобы не грузить систему
					time.sleep(0.5)
		except Exception as e:
			l.exception(e)
	finally:
		#Завершаем сессию - выдаем внесенные деньги обратно
		l.EndSession()
		#Тут могут появиться события по выдаче сдачи или ошибки устройств
		l.join()
