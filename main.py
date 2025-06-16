import math
from enum import Enum
import pygame as pg
from tkinter import filedialog
from tkinter import messagebox
import tkinter
import os
import sys
from pygame import Surface


class HitObject:
    x: int = 0
    y: int = 0
    time: int = 0
    type: int = 0  # bit flags
    hit_sound: int = 0  # bit flags
    object_params: str = ""  # comma separated values
    hit_sample: str = ""  # colon separated values

    o_hit_circle: bool = False
    o_slider: bool = False
    o_new_combo: bool = False
    o_spinner: bool = False
    o_colour_hax: str = ""
    o_mania_hold: bool = False

    om_end_time: int = 0  # for mania hold notes

    def parse(self, s: str):
        params: list[str] = s.split(",")
        self.x = int(params[0])
        self.y = int(params[1])
        self.time = int(params[2])
        self.type = int(params[3])

        # type parsing
        bits = format(int(self.type), "09b")
        list_bits = []
        for i in range(0, len(bits) - 1):
            list_bits.append(bits[-(i + 1)])

        self.o_hit_circle: bool = list_bits[0] == "1"
        self.o_slider: bool = list_bits[1] == "1"
        self.o_new_combo: bool = list_bits[2] == "1"
        self.o_spinner: bool = list_bits[3] == "1"
        self.o_colour_hax: str = list_bits[4] + list_bits[5] + list_bits[6]
        self.o_mania_hold: bool = list_bits[7] == "1"

        self.hit_sound = int(params[4])

        self.object_params = str(params[-1])

        # if mania_hold
        if self.o_mania_hold:
            self.om_end_time = int(self.object_params.split(":")[0])
            self.hit_sample = str(self.object_params.split(":")[:-1])
        else:
            self.om_end_time = 0
            self.hit_sample = str(self.object_params)


class Note:
    start_time: int = 0
    note_type: int = 0
    key_index: int = 0
    is_last_note: bool = False
    end_time: int = 0
    hold_length: int = 0

    def set_note(self, start_time, key_index):
        self.start_time = start_time
        self.note_type = 0
        self.key_index = key_index

    def set_hold_note(self, start_time, end_time, key_index):
        self.start_time = start_time
        self.note_type = 1
        self.end_time = end_time
        self.hold_length = end_time - start_time
        self.key_index = key_index


def read_beatmap_file(beatmap_path: str) -> list[Note]:
    with open(beatmap_path, "r", encoding="UTF-8") as f:
        content = f.readlines()
        notes = []

        start_read = False
        while len(content) > 0:
            line = content.pop(0).strip()

            if start_read:
                if line == "":
                    start_read = False
                    continue

                hit_object = HitObject()
                hit_object.parse(line.strip())

                if hit_object.o_mania_hold:
                    note = Note()
                    column_index = math.floor(hit_object.x * 4 / 512)
                    column_index = max(0, min(3, column_index))
                    note.set_hold_note(
                        hit_object.time, hit_object.om_end_time, column_index
                    )
                    notes.append(note)
                else:
                    note = Note()
                    column_index = math.floor(hit_object.x * 4 / 512)
                    column_index = max(0, min(3, column_index))
                    note.set_note(hit_object.time, column_index)
                    notes.append(note)
            else:
                if line.startswith("[HitObjects]"):
                    start_read = True
                    continue

                if line == "":
                    start_read = False
                    continue

    return notes


notePos = None
note_list: list = []
k1list = []
k2list = []
k3list = []
k4list = []


def get_audio_file_name(beatmap_path: str):
    with open(beatmap_path, "r", encoding="UTF-8") as f:
        content = f.readlines()
        for line in content:
            if line.startswith("AudioFilename:"):
                filename = line.split(":")[1].strip()
                return filename.lstrip()


def setup(beatmap):
    global notePos, k1list, k2list, k3list, k4list, note_list
    note_list = read_beatmap_file(beatmap)
    k1list = []
    k2list = []
    k3list = []
    k4list = []


def spawn_note(time: float):
    # time 이 [생성전 대기중인 노트리스트] 0번의 스폰시간을 넘었으면
    if len(note_list) != 0:
        if time >= note_list[0].start_time - 4000:
            if len(note_list) == 1:
                note_list[0].is_last_note = True
            if note_list[0].key_index == 0:
                k1list.append(note_list.pop(0))  # 해당하는 키 리스트에 넣는다
            elif note_list[0].key_index == 1:
                k2list.append(note_list.pop(0))
            elif note_list[0].key_index == 2:
                k3list.append(note_list.pop(0))
            elif note_list[0].key_index == 3:
                k4list.append(note_list.pop(0))


def check_miss(index, time):
    if time > index.start_time + 124.5:
        # print("MISS / ", game_time - i.startTime)
        if index.key_index == 0:
            k1list.remove(index)
        elif index.key_index == 1:
            k2list.remove(index)
        elif index.key_index == 2:
            k3list.remove(index)
        elif index.key_index == 3:
            k4list.remove(index)
        return True
    else:
        return False


duration = 500  # 스크롤 속도
user_select = ""  # 선택한 비트맵
user_select_dir = ""  # 선택한 비트맵 폴더

game_time = -3


def play():
    return True


def pause():
    return False


def restart():
    global game_time
    game_time = -3


def level_select():
    global user_select
    global user_select_dir

    root = tkinter.Tk()
    root.overrideredirect(True)
    root.attributes("-alpha", 0)
    # files 변수에 선택 파일 경로 넣기
    files = filedialog.askopenfilename(
        title="비트맵 파일을 선택해 주세요", filetypes=[("비트맵 파일", "*.osu")]
    )
    root.destroy()

    if files == "":
        # 파일 선택 안했을 때 종료 확인 메세지 출력
        ask_result = messagebox.askyesno("메세지", "게임을 종료하시겠습니까?")
        if ask_result:
            sys.exit()
        else:
            level_select()
            return

    user_select = files
    user_select_dir = os.path.dirname(files)


game_icon = pg.image.load("skin/osulogo.png")
note1 = pg.image.load("skin/mania-note1.png")  # 노트 리소스
note2 = pg.image.load("skin/mania-note2.png")  # 노트 리소스
note3 = pg.image.load("skin/mania-note2.png")  # 노트 리소스
note4 = pg.image.load("skin/mania-note1.png")  # 노트 리소스
stage_right = pg.image.load("skin/mania-stage-right.png")  # UI 리소스
stage_left = pg.image.load("skin/mania-stage-left.png")  # UI 리소스
stage_hint = pg.image.load("skin/mania-stage-hint.png")  # 판정선 리소스
hit0 = pg.image.load("skin/mania-hit0.png")  # hit 0 리소스
hit50 = pg.image.load("skin/mania-hit50.png")  # hit 50 리소스
hit100 = pg.image.load("skin/mania-hit100.png")  # hit 100 리소스
hit200 = pg.image.load("skin/mania-hit200.png")  # hit 200 리소스
hit300 = pg.image.load("skin/mania-hit300.png")  # hit 300 리소스
hit300g = pg.image.load("skin/mania-hit300g-0.png")  # hit 300g 리소스

rankSS = pg.image.load("skin/ranking-X.png")
rankS = pg.image.load("skin/ranking-S.png")
rankA = pg.image.load("skin/ranking-A.png")
rankB = pg.image.load("skin/ranking-B.png")
rankC = pg.image.load("skin/ranking-C.png")
rankD = pg.image.load("skin/ranking-D.png")

score0 = pg.image.load("skin/score0.png")  # 숫자 이미지
score1 = pg.image.load("skin/score1.png")  # 숫자 이미지
score2 = pg.image.load("skin/score2.png")  # 숫자 이미지
score3 = pg.image.load("skin/score3.png")  # 숫자 이미지
score4 = pg.image.load("skin/score4.png")  # 숫자 이미지
score5 = pg.image.load("skin/score5.png")  # 숫자 이미지
score6 = pg.image.load("skin/score6.png")  # 숫자 이미지
score7 = pg.image.load("skin/score7.png")  # 숫자 이미지
score8 = pg.image.load("skin/score8.png")  # 숫자 이미지
score9 = pg.image.load("skin/score9.png")  # 숫자 이미지
scores_resources = [
    score0,
    score1,
    score2,
    score3,
    score4,
    score5,
    score6,
    score7,
    score8,
    score9,
]

default0 = pg.image.load("skin/default-0.png")
default1 = pg.image.load("skin/default-1.png")
default2 = pg.image.load("skin/default-2.png")
default3 = pg.image.load("skin/default-3.png")
default4 = pg.image.load("skin/default-4.png")
default5 = pg.image.load("skin/default-5.png")
default6 = pg.image.load("skin/default-6.png")
default7 = pg.image.load("skin/default-7.png")
default8 = pg.image.load("skin/default-8.png")
default9 = pg.image.load("skin/default-9.png")
numbers_default = [
    default0,
    default1,
    default2,
    default3,
    default4,
    default5,
    default6,
    default7,
    default8,
    default9,
]

note1 = pg.transform.scale(note1, (150, 50))  # 노트1 오브젝트 생성
note2 = pg.transform.scale(note2, (150, 50))  # 노트2 오브젝트 생성
note3 = pg.transform.scale(note3, (150, 50))  # 노트3 오브젝트 생성
note4 = pg.transform.scale(note4, (150, 50))  # 노트4 오브젝트 생성
stage_right = pg.transform.scale(stage_right, (8, 1000))  # UI 오브젝트 생성
stage_left = pg.transform.scale(stage_left, (8, 1000))  # UI 오브젝트 생성
stage_hint = pg.transform.scale(stage_hint, (600, 100))  # 판정선 생성

pg.font.init()
# print(pg.font.get_fonts()) # 사용가능한 폰트 목록 출력
sysFont = pg.font.SysFont("malgungothic", 30, False, False)

display = pg.display.set_mode((608, 1000))  # 해상도 설정
pg.display.set_caption("pasu!")  # 타이틀
pg.display.set_icon(game_icon)  # 아이콘

pg.mixer.pre_init(48000, -16, 2, 256)  # 파이게임 오디오 초기화
pg.mixer.init(48000, -16, 2, 256)
print(pg.mixer.get_init())
offset_by_audio_buffer = 256 * 1 / 48000 * 1000
print(offset_by_audio_buffer)
game_offset = 50

pg.init()  # pygame 초기화

level_select()  # 맵 선택
setup(user_select)

beatmapSongFileName = get_audio_file_name(user_select)  # 음악 파일 이름 가져오기
beatmapDir = user_select_dir  # 비트맵 디렉터리 가져오기

pg.mixer.music.load(f"{beatmapDir}/{beatmapSongFileName}")  # 음악 리소스 불러오기
pg.mixer.music.set_volume(0.04)

clock = pg.time.Clock()
game_time -= int(offset_by_audio_buffer + game_offset)

isPlay = False
running = True
isPause = False
frameRate = 1000
isEnded = False
endDelayTime = 3000

# 인게임 시스템 변수
total_notes = len(note_list)
score = 0  # 게임 점수
max_score = 1000000  # 최대 점수
Bonus = 100
perfect_position = 800  # 판정 선
last_accuracy = hit0
last_accuracy_exposure_time = 0  # 마지막 판정의 노출 시간
combo = 0
hitValues = [0, 0, 0, 0, 0, 0]  # MISS,50,100,200,300,MAX

pressed_key = [False, False, False, False]  # 키 입력 체크 (추후 사용)


class Screen(Enum):  # 화면 변수
    MainMenu = 0
    GamePlay = 1
    ResultScreen = 2


now_screen = Screen(1)


def get_hold_note_size(base_height: float, start_pos: float, end_pos: float) -> float:
    fill_height = start_pos - end_pos

    return fill_height + base_height


def calculate_score(score_max, notes_total, current_judge):  # 점수계산
    global Bonus
    hit_base: tuple
    if current_judge == "MAX":
        hit_base = ("MAX", 320, 32, 2, 0)
    elif current_judge == "300":
        hit_base = ("300", 300, 32, 1, 0)
    elif current_judge == "200":
        hit_base = ("200", 200, 16, 0, 8)
    elif current_judge == "100":
        hit_base = ("100", 100, 8, 0, 24)
    elif current_judge == "50":
        hit_base = ("50", 50, 4, 0, 44)
    else:
        return 0
    base_score = (score_max * 0.5 / notes_total) * (hit_base[1] / 320)
    Bonus = Bonus + hit_base[3] - hit_base[4]
    if Bonus > 100:
        Bonus = 100
    elif Bonus < 0:
        Bonus = 0
    bonus_score = (score_max * 0.5 / notes_total) * (
        hit_base[2] * math.sqrt(Bonus) / 320
    )
    result = base_score + bonus_score
    return result


def calculate_accuracy(hits_counts: list):
    total_points_of_hits = (
        hits_counts[1] * 50
        + hits_counts[2] * 100
        + hits_counts[3] * 200
        + hits_counts[4] * 300
        + hits_counts[5] * 300
    )
    total_number_of_hits = (
        hits_counts[0]
        + hits_counts[1]
        + hits_counts[2]
        + hits_counts[3]
        + hits_counts[4]
        + hits_counts[5]
    )
    result = total_points_of_hits / (total_number_of_hits * 300)
    result = math.floor(result * 10000) / 100
    return result


def calculate_play_rank(accu):
    if accu >= 100:
        return "SS"
    if accu >= 95:
        return "S"
    if accu >= 90:
        return "A"
    if accu >= 80:
        return "B"
    if accu >= 70:
        return "C"
    else:
        return "D"


# 위치계산 함수들
def get_center_nums(target_digit, all_digit):  # 콤보 띄우는 이미지
    global score0  # 대표적인 숫자 콤보 이미지 변수
    return (
        608 / 2
        - (score0.get_width() / 2) * all_digit
        + target_digit * score0.get_width()
    )


def get_center_nums_score(target_digit, all_digit):  # 스코어 띄우는 이미지
    global default0  # 대표적인 숫자 스코어 이미지 변수
    return (
        608 / 2
        - (default0.get_width() / 2) * all_digit
        + target_digit * default0.get_width()
    )


def get_horizontal_center_position_from_img(img):
    return 608 / 2 - (img.get_width() / 2)


def render_note(note_data: Note) -> None:
    global perfect_position

    pos_x: int
    obj: Surface

    if note_data.key_index == 0:
        pos_x = 0
        obj = note1
    elif note_data.key_index == 1:
        pos_x = 150
        obj = note2
    elif note_data.key_index == 2:
        pos_x = 300
        obj = note3
    elif note_data.key_index == 3:
        pos_x = 450
        obj = note4
    else:
        return

    pos = 0 + perfect_position * (
        (game_time - note_data.start_time + duration) / duration
    )
    if note_data.note_type == 1:
        end_pos = 0 + perfect_position * (
            (game_time - note_data.end_time + duration) / duration
        )
        long_obj = pg.transform.scale(obj, (150, get_hold_note_size(50, pos, end_pos)))
        display.blit(long_obj, (pos_x, pos - long_obj.get_height() + 50))
    else:
        display.blit(obj, (pos_x, pos))


def on_lane_up(lane_note_list: list, lane_index: int) -> None:
    pressed_key[lane_index] = False
    pass


def on_lane_input(lane_note_list: list, lane_index: int) -> None:
    global last_accuracy, last_accuracy_exposure_time, score, combo, isEnded
    pressed_key[lane_index] = True
    if len(lane_note_list) != 0:
        input_time = game_time - lane_note_list[0].start_time
        if 16.5 >= input_time >= -16.5:
            print("MAX / ", input_time)
            last_accuracy = hit300g
            last_accuracy_exposure_time = 500
            score += calculate_score(max_score, total_notes, "MAX")
            combo += 1
            hitValues[5] += 1
            if lane_note_list[0].is_last_note:
                isEnded = True
            lane_note_list.pop(0)
        elif 37.5 >= input_time >= -37.5:
            print("300 / ", input_time)
            last_accuracy = hit300
            last_accuracy_exposure_time = 500
            score += calculate_score(max_score, total_notes, "300")
            combo += 1
            hitValues[4] += 1
            if lane_note_list[0].is_last_note:
                isEnded = True
            lane_note_list.pop(0)
        elif 70.5 >= input_time >= -70.5:
            print("200 / ", input_time)
            last_accuracy = hit200
            last_accuracy_exposure_time = 500
            score += calculate_score(max_score, total_notes, "200")
            combo += 1
            hitValues[3] += 1
            if lane_note_list[0].is_last_note:
                isEnded = True
            lane_note_list.pop(0)
        elif 100.5 >= input_time >= -100.5:
            print("100 / ", input_time)
            last_accuracy = hit100
            last_accuracy_exposure_time = 500
            score += calculate_score(max_score, total_notes, "100")
            combo += 1
            hitValues[2] += 1
            if lane_note_list[0].is_last_note:
                isEnded = True
            lane_note_list.pop(0)
        elif 124.5 >= input_time >= -124.5:
            print("50 / ", input_time)
            last_accuracy = hit50
            last_accuracy_exposure_time = 500
            score += calculate_score(max_score, total_notes, "50")
            combo += 1
            hitValues[1] += 1
            if lane_note_list[0].is_last_note:
                isEnded = True
            lane_note_list.pop(0)


def judging_note(note_data: Note) -> None:
    global last_accuracy, last_accuracy_exposure_time, score, combo, isEnded

    if check_miss(note_data, game_time):
        last_accuracy = hit0
        last_accuracy_exposure_time = 500
        combo = 0
        hitValues[0] += 1
        if note_data.is_last_note:
            isEnded = True
    else:
        render_note(note_data)


def on_update():
    global last_accuracy, last_accuracy_exposure_time, combo, isPlay, game_time, isEnded

    if isPlay:
        game_time += clock.get_time()  # 0부터 지금까지의 시간을 저장

    spawn_note(game_time)
    for note_data in k1list:
        judging_note(note_data)
    for note_data in k2list:
        judging_note(note_data)
    for note_data in k3list:
        judging_note(note_data)
    for note_data in k4list:
        judging_note(note_data)


last_text_exposure_time = 0
system_msg_to_display = ""
show_fps_text = True

while running:
    clock.tick(frameRate)  # 프레임 제한
    game_time = game_time

    for event in pg.event.get():  # 파이게임 이벤트
        if event.type == pg.QUIT:
            running = False
        elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            running = False
        elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
            if not isPlay:
                isPlay = play()
                if isPause:
                    isPause = False
                    pg.mixer.music.unpause()
                    last_text_exposure_time = 1500
                    system_msg_to_display = "재개"
                else:
                    pg.mixer.music.play()
            else:
                pg.mixer.music.pause()
                isPlay = pause()
                isPause = True
                last_text_exposure_time = 1500
                system_msg_to_display = "일시정지"
        elif event.type == pg.KEYDOWN and event.key == pg.K_r:
            pg.mixer.music.stop()
            setup(user_select)
            restart()
            last_accuracy_exposure_time = 0
            score = 0
            Bonus = 100
            combo = 0
            pressed_key = [False, False, False, False]
            isPause = False
            isPlay = play()
            pg.mixer.music.play()
            last_text_exposure_time = 1500
            system_msg_to_display = "재시작"
            continue
        elif event.type == pg.KEYDOWN and event.key == pg.K_2:
            duration -= 50
            if duration < 50:
                duration = 50
            last_text_exposure_time = 1500
            system_msg_to_display = f"노트 이동시간 - {duration}"
        elif event.type == pg.KEYDOWN and event.key == pg.K_1:
            duration += 50
            if duration > 4000:
                duration = 4000
            last_text_exposure_time = 1500
            system_msg_to_display = f"노트 이동시간 - {duration}"
        elif event.type == pg.KEYDOWN and event.key == pg.K_d:  # 1번 키 (인덱스 0)
            if isPlay:
                on_lane_input(k1list, 0)
        elif event.type == pg.KEYDOWN and event.key == pg.K_f:  # 2번 키 (인덱스 1)
            if isPlay:
                on_lane_input(k2list, 1)
        elif event.type == pg.KEYDOWN and event.key == pg.K_j:  # 3번 키 (인덱스 2)
            if isPlay:
                on_lane_input(k3list, 2)
        elif event.type == pg.KEYDOWN and event.key == pg.K_k:  # 4번 키 (인덱스 3)
            if isPlay:
                on_lane_input(k4list, 3)
        elif event.type == pg.KEYUP and event.key == pg.K_d:
            if isPlay:
                on_lane_up(k1list, 0)
        elif event.type == pg.KEYUP and event.key == pg.K_f:
            if isPlay:
                on_lane_up(k2list, 1)
        elif event.type == pg.KEYUP and event.key == pg.K_j:
            if isPlay:
                on_lane_up(k3list, 2)
        elif event.type == pg.KEYUP and event.key == pg.K_k:
            if isPlay:
                on_lane_up(k4list, 3)
        elif event.type == pg.KEYDOWN and event.key == pg.K_F7:
            show_fps_text = not show_fps_text
            last_text_exposure_time = 1500
            if show_fps_text:
                system_msg_to_display = "FPS 표시 켜기"
            else:
                system_msg_to_display = "FPS 표시 끄기"
    if now_screen == Screen(0):  # 메인메뉴
        print("현재 메인메뉴 입니다.")
    elif now_screen == Screen(1):  # 인게임
        display.fill((0, 0, 0))  # 검은색으로 채우기
        display.blit(
            stage_hint, ((608 - stage_hint.get_width()) / 2, 800)
        )  # 판정선 그리기
        display.blit(stage_right, (600, 0))  # 스테이지 오른쪽 그리기
        display.blit(stage_left, (0, 0))  # 스테이지 왼쪽 그리기

        on_update()  # 매 프레임마다 동작

        if show_fps_text:
            fps_str = f"{int(clock.get_fps())} FPS"
            fps_text = sysFont.render(fps_str, True, (255, 255, 255))
            display.blit(fps_text, (608 - fps_text.get_width(), 0))

        if last_text_exposure_time > 0:
            last_text_exposure_time -= clock.get_time()
            text = sysFont.render(system_msg_to_display, True, (255, 255, 255))
            display.blit(text, (0, 0))

        if isEnded:
            if endDelayTime > 0:
                endDelayTime -= clock.get_time()
            else:
                now_screen = Screen(2)
                pg.mixer.music.fadeout(1500)
                print("결과창")

        # 현재 콤보 표시
        if combo > 0:  # 콤보가 0보다 클때
            for i in range(
                0, len(str(combo))
            ):  # 현재 콤보를 문자열로 변환 후 문자의 개수를 가져옴
                display.blit(
                    scores_resources[int(str(combo)[i])],
                    (get_center_nums(i, len(str(combo))), 200),
                )
                # 숫자 이미지를 리스트로 담은 scores_resources에서 이미지를 가져옴
                # 현재콤보를 문자열로 만들어서 문자의 개수를 구한 뒤, 함수 사용 (i는 몇 번째에 있는 문자인가)

        if last_accuracy_exposure_time > 0:
            last_accuracy_exposure_time -= clock.get_time()
            if last_accuracy == hit300g:
                display.blit(
                    last_accuracy,
                    (get_horizontal_center_position_from_img(last_accuracy), 500),
                )
            if last_accuracy == hit300:
                display.blit(
                    last_accuracy,
                    (get_horizontal_center_position_from_img(last_accuracy), 500),
                )
            if last_accuracy == hit200:
                display.blit(
                    last_accuracy,
                    (get_horizontal_center_position_from_img(last_accuracy), 500),
                )
            if last_accuracy == hit100:
                display.blit(
                    last_accuracy,
                    (get_horizontal_center_position_from_img(last_accuracy), 500),
                )
            if last_accuracy == hit50:
                display.blit(
                    last_accuracy,
                    (get_horizontal_center_position_from_img(last_accuracy), 500),
                )
            if last_accuracy == hit0:
                display.blit(
                    last_accuracy,
                    (get_horizontal_center_position_from_img(last_accuracy), 500),
                )
    elif now_screen == Screen(2):  # 결과창일때
        display.fill((0, 0, 0))
        accuracy = calculate_accuracy(hitValues)
        if score > 0:
            for i in range(0, len(str(math.floor(score)))):
                display.blit(
                    numbers_default[int(str(math.floor(score))[i])],
                    (get_center_nums_score(i, len(str(math.floor(score)))), 500),
                )
        if calculate_play_rank(accuracy) == "SS":
            display.blit(rankSS, (get_horizontal_center_position_from_img(rankSS), 200))
        elif calculate_play_rank(accuracy) == "S":
            display.blit(rankS, (get_horizontal_center_position_from_img(rankS), 200))
        elif calculate_play_rank(accuracy) == "A":
            display.blit(rankA, (get_horizontal_center_position_from_img(rankA), 200))
        elif calculate_play_rank(accuracy) == "B":
            display.blit(rankB, (get_horizontal_center_position_from_img(rankB), 200))
        elif calculate_play_rank(accuracy) == "C":
            display.blit(rankC, (get_horizontal_center_position_from_img(rankC), 200))
        elif calculate_play_rank(accuracy) == "D":
            display.blit(rankD, (get_horizontal_center_position_from_img(rankD), 200))
        print("점수:", math.floor(score))
        print("정확도:", accuracy)
        print("랭크:", calculate_play_rank(accuracy))
    pg.display.update()

pg.quit()
sys.exit()
