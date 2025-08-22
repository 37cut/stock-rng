import random
import os.path
import warnings
import mplcursors
import matplotlib.pyplot as mp
import matplotlib.font_manager as mf

warnings.filterwarnings('ignore', category = UserWarning)

path = os.path.dirname(__file__)

def generate_code(size: int) -> set:
    cset = set()
    locate_code = ['600', '601', '603',
                   '300', '301', '000',
                   '001', '002', '003']

    while len(cset) != size:
        seed = str(random.randint(100, 65535) * random.randint(100, 65535))
        x = random.randint(0, len(seed) - 4)
        y = x + 3
        cset.add(locate_code[random.randint(0, 8)] + seed[x:y])

    print('> Stock RNG v1.3')
    print('> This program requires a network connection to proceed')
    print('> Prevent to close this program while processing data' + '\n')

    return cset

def dot2f(x) -> float:
    value = 0
    if isinstance(x, float):
        value = float(format(x, '.2f'))

    return value

class Canva:
    def __init__(self, period: int, coord: tuple, ax: list):
        self.period = period
        self.coord  = coord
        self.ax     = ax
        self.left   = self.coord[0]
        self.right  = self.coord[1]

        self.__default_coord = (-2, self.period + 1)

        self.move_scale = int(self.period * 0.05)

    def refresh(self):
        [ self.ax[idx].set_xlim(self.coord) for idx in range(len(self.ax)) ]
        mp.draw()

    def decrease_view(self):
        self.left -= self.move_scale
        self.right += self.move_scale

        if self.left + self.move_scale <= self.__default_coord[0] \
        or self.right - self.move_scale >= self.__default_coord[1]:
            self.left, self.right = self.__default_coord
        self.coord = (self.left, self.right)
        self.refresh()

    def increase_view(self):
        self.left += self.move_scale
        self.right -= self.move_scale

        if self.left + self.move_scale >= self.right:
            self.left, self.right = self.coord
        self.coord = (self.left, self.right)
        self.refresh()

    def to_left(self):
        self.left -= self.move_scale
        self.right -= self.move_scale

        if self.left + self.move_scale <= self.__default_coord[0]:
            self.left, self.right = self.__default_coord
        self.coord = (self.left, self.right)
        self.refresh()

    def to_right(self):
        self.left += self.move_scale
        self.right += self.move_scale

        if self.right - self.move_scale >= self.__default_coord[1]:
            self.left, self.right = self.__default_coord
        self.coord = (self.left, self.right)
        self.refresh()

    def adjust_graph(self, match: str):
        method = {
            'up':       self.decrease_view,
            'down':     self.increase_view,
            'left':     self.to_left,
            'right':    self.to_right}
        return method.get(match, lambda: '')()

class Stock:
    def __init__(self, meta: list, sub: dict):
        self.meta = meta
        self.sub = sub

        fmap = lambda col: list(map(float, col))

        self.code = self.meta['code']
        self.name = self.meta['name']
        self.market = self.meta['bk_name']

        self.time    = self.sub[:,0]
        self.start   = fmap(self.sub[:,1])
        self.end     = fmap(self.sub[:,2])
        self.max     = fmap(self.sub[:,3])
        self.min     = fmap(self.sub[:,4])
        self.volume  = fmap(self.sub[:,5])
        self.percent = fmap(self.sub[:,6])

        self.period  = len(self.time)
        self.scale   = int(self.period * 0.125) if self.period >= 16 else 1

        maximum_price = max(self.max, default = 0)
        minimum_price = min(self.min, default = 0)
        maximum_percent = max(self.percent, default = 0)
        minimum_percent = min(self.percent, default = 0)

        maximum_volume = max(self.volume, default = 0)

        self.vScale_1 = ( dot2f(1.03 * minimum_price - 0.03 * maximum_price),
                          dot2f(1.03 * maximum_price - 0.03 * minimum_price) )
        self.vScale_2 = ( dot2f(1.1 * minimum_percent - 0.1 * maximum_percent),
                          dot2f(1.1 * maximum_percent - 0.1 * minimum_percent) )
        self.vScale_3 = ( 0, dot2f(1.05 * maximum_volume) )

        self.hScale = ( -2, self.period + 1 )
        self.vScale = ( self.vScale_1, self.vScale_2, self.vScale_3 )

        print(f'> Code: {self.code}')

    def show(self):
        font_regl = mf.FontProperties(fname = path + '/fonts/font.otf', size = 16)
        font_mono = mf.FontProperties(fname = path + '/fonts/mono.ttf', size = 14)

        kline_label = ['Start Price', 'End Price', 'Max Price', 'Min Price']
        title_color = '#009900' if self.end[0] > self.end[-1] else '#990000'

        tab = '   '

        # layout
        self.fig, self.ax = mp.subplots(nrows = 3, ncols = 1,
                                        constrained_layout = True,
                                        gridspec_kw = dict(height_ratios = [6,1,1]))

        self.canva = Canva(self.period, self.hScale, self.ax)

        self.fig.suptitle(f'{self.code}, {self.name} [ {self.market} ]', fontproperties = font_regl)

        # event connect
        self.fig.canvas.mpl_connect('scroll_event', self.mouse_input)
        self.fig.canvas.mpl_connect('key_press_event', self.key_input)

        # set scale
        for idx in range(len(self.ax)):
            self.ax[idx].set_xlim(self.hScale)
            self.ax[idx].set_ylim(self.vScale[idx])
            self.ax[idx].xaxis.set_major_locator(mp.MultipleLocator(self.scale))

        # plot kline
        self.ax[0].set_title(label = f'Last updated price: {self.end[-1]}{tab}',
                             color = title_color, fontproperties = font_mono)

        self.ax[0].plot(self.time, self.start, label = kline_label[0])
        self.ax[0].plot(self.time, self.end, label = kline_label[1])
        self.ax[0].plot(self.time, self.max,
                        color = 'r',
                        marker = '.',
                        linestyle = 'dotted',
                        label = kline_label[2])
        self.ax[0].plot(self.time, self.min,
                        color = 'g',
                        marker = '.',
                        linestyle = 'dotted',
                        label = kline_label[3])

        self.ax[0].legend(loc = 'best', labels = kline_label)

        # plot percentage
        self.ax[1].set_title(f'Last updated percentage: {self.percent[-1]}{tab}',
                             fontproperties = font_mono)

        self.ax[1].plot(self.time, self.percent,
                        color = 'c',
                        linestyle = 'solid',
                        label = 'Percent')

        self.ax[1].legend(loc = 'best', labels = ['Percent'])

        # plot volume
        self.ax[2].set_title(f'Last updated volume: {self.volume[-1]}{tab}',
                             fontproperties = font_mono)
        self.ax[2].bar(self.time, self.volume, label = 'Volume')
        self.ax[2].legend(loc = 'best', labels = ['Volume'])

        mplcursors.cursor()

        mp.show()
        mp.close()

    def mouse_input(self, event):
        if event: self.canva.adjust_graph(event.button)

    def key_input(self, event):
        if event: self.canva.adjust_graph(event.key)
