import pytest

from datetime import datetime
from datetime import timedelta
from os.path import dirname
from os.path import join
from storm.locals import *

from bosco.course import Control
from bosco.course import Course
from bosco.course import SIStation
from bosco.editor import RunFinder
from bosco.event import RelayEvent
from bosco.event import Relay24hEvent
from bosco.importer import OCADXMLCourseImporter
from bosco.importer import SIRunImporter
from bosco.importer import Team24hImporter
from bosco.ranking import Cache
from bosco.run import Punch
from bosco.run import Run
from bosco.runner import Category
from bosco.runner import Runner
from bosco.runner import SICard
from bosco.runner import Team


class TestEvent:

    def __init__(self, store):

        self._store = store

        # create control with 2 sistations
        c200 = Control('200', SIStation(200))
        c200.sistations.add(SIStation(201))
        self._c131 = self._store.add(Control('131', SIStation(131)))

        # create sistation without any control
        self._store.add(SIStation(133))

        # create sistation and control not in course
        self._store.add(Control('134', store = self._store))

        # Create a Course
        self._course = self._store.add(Course('A', length = 1679, climb = 587))
        self._course.extend(['131', '132', c200, '132'])

        # Add additional course for RelayEvent testing, they have the same
        # controls
        c = self._store.add(Course('B', length = 1679, climb = 587))
        c.extend(['131', '132', c200, '132'])
        c = self._store.add(Course('C', length = 1679, climb = 587))
        c.extend(['131', '132', c200, '132'])

        # Add additional course for RoundCountScoreing
        c = self._store.add(Course('D', length = 0, climb = 0))
        c.extend(['131', c200])
        c = self._store.add(Course('E', length = 0, climb = 0))
        c.extend([c200])

        # Create categorys
        self._cat_ind = self._store.add(Category('HAM'))
        cat_team = Category('D135')

        # Create Runners
        self._runners = []

        self._runners.append(Runner('Muster', 'Hans', SICard(655465),
                                    self._cat_ind, '101'))
        self._runners.append(Runner('Gerster', 'Trudi', SICard(765477),
                                    self._cat_ind, '102'))
        self._runners.append(Runner('Mueller', 'Hans', SICard(768765),
                                    self._cat_ind, '103'))
        self._runners.append(Runner('Missing', 'The', SICard(113456),
                                    self._cat_ind))
        self._runners.append(Runner('Gugus', 'Dada', SICard(56789),
                                    self._cat_ind))
        self._runners.append(Runner('Al', 'Missing', SICard(12345),
                                    self._cat_ind))

        # Create a team
        self._team = Team('1', 'The best team ever', category= cat_team)
        self._team.members.add(self._runners[0])
        self._team.members.add(self._runners[1])
        self._team.members.add(self._runners[2])

        # some times we use in several places
        self._team_start_time = datetime(2008, 3, 19, 8, 15, 00)
        self._team_finish_time = datetime(2008, 3, 19, 8, 36, 25)
        self._team_time = self._team_finish_time - self._team_start_time

        # Create a runs
        self._runs = []

        # double start and finish punches, punch on sistation 201 for
        # control 200
        self._runs.append(
            Run(655465,
                'A',
                [(131, datetime(2008, 3, 19, 8, 22, 39)),
                 (132, datetime(2008, 3, 19, 8, 23, 35)),
                 (201, datetime(2008, 3, 19, 8, 24, 35)),
                 (132, datetime(2008, 3, 19, 8, 25, 0)),
                ],
                card_start_time = datetime(2008, 3, 19, 8, 20, 32),
                card_finish_time = datetime(2008, 3, 19, 8, 25, 37),
                store = self._store
            )
        )
        self._runs[0].manual_start_time = datetime(2008, 3, 19, 8, 20, 35)
        self._runs[0].manual_finish_time = datetime(2008, 3, 19, 8, 25, 35)
        self._runs[0].complete = True

        # normal run
        self._runs.append(
            Run(765477,
                'A',
                [(131, datetime(2008, 3, 19, 8, 27, 39)),
                 (132, datetime(2008, 3, 19, 8, 28, 35)),
                 (200, datetime(2008, 3, 19, 8, 29, 35)),
                 (132, datetime(2008, 3, 19, 8, 30, 0)),
                ],
                card_start_time = datetime(2008, 3, 19, 8, 25, 50),
                card_finish_time = datetime(2008, 3, 19, 8, 31, 23),
                store = self._store
            )
        )
        self._runs[1].complete = True

        # normal run, punching additional sistation not connected to any
        # control (133) and additional control (134)
        self._runs.append(
            Run(768765,
                'A',
                [ (131, datetime(2008, 3, 19, 8, 33, 39)),
                  (132, datetime(2008, 3, 19, 8, 34, 35)),
                  (133, datetime(2008, 3, 19, 8, 34, 50)),
                  (200, datetime(2008, 3, 19, 8, 35, 35)),
                  (134, datetime(2008, 3, 19, 8, 35, 50)),
                  (132, datetime(2008, 3, 19, 8, 36, 0)),
                ],
                card_start_time = datetime(2008, 3, 19, 8, 31, 25),
                card_finish_time = datetime(2008, 3, 19, 8, 36, 25),
                store = self._store
            )
        )
        self._runs[2].complete = True

        # punch on control 131 missing
        self._runs.append(
            Run(113456,
                'A',
                [ (132, datetime(2008, 3, 19, 8, 33, 39)),
                  (200, datetime(2008, 3, 19, 8, 35, 35)),
                  (132, datetime(2008, 3, 19, 8, 36, 0)),
                ],
                card_start_time = datetime(2008, 3, 19, 8, 31, 25),
                card_finish_time = datetime(2008, 3, 19, 8, 36, 25),
                store = self._store
            )
        )
        self._runs[3].complete = True

        # This run ends after run 0 but before the first punch of run 1
        self._runs.append(
            Run(56789,
                'A',
                [(131, datetime(2008, 3, 19, 8, 22, 39)),
                 (132, datetime(2008, 3, 19, 8, 23, 35)),
                 (201, datetime(2008, 3, 19, 8, 24, 35)),
                 (132, datetime(2008, 3, 19, 8, 25, 0)),
                ],
                card_start_time = datetime(2008, 3, 19, 8, 20, 32),
                card_finish_time = datetime(2008, 3, 19, 8, 25, 40),
                store = self._store
            )
        )
        self._runs[4].complete = True

        # empty run
        self._runs.append(Run(12345, 'A', [], store = self._store))
        self._runs[5].complete = True

        # run without runner and course
        self._runs.append(
            Run(SICard(9999),
                None,
                [(131, datetime(2008, 3, 19, 8, 22, 39)),
                 (132, datetime(2008, 3, 19, 8, 23, 35)),
                 (201, datetime(2008, 3, 19, 8, 24, 35)),
                 (132, datetime(2008, 3, 19, 8, 25, 0)),
                ],
                card_start_time = datetime(2008, 3, 19, 8, 20, 32),
                card_finish_time = datetime(2008, 3, 19, 8, 25, 40),
                store = self._store
            )
        )
        self._runs[6].complete = True

        # runs for RoundCountScoreing tests, sistation 200 and 201 are at the
        # same control!

        # course with 2 controls, 3 rounds
        self._runs.append(
            Run(SICard(10),
                None,
                [(131, datetime(2008, 3, 19, 8, 22, 29)),
                 (200, datetime(2008, 3, 19, 8, 23, 30)),
                 (131, datetime(2008, 3, 19, 8, 24, 29)),
                 (201, datetime(2008, 3, 19, 8, 25, 30)),
                 (131, datetime(2008, 3, 19, 8, 25, 50)),
                 (200, datetime(2008, 3, 19, 8, 26, 30)),
                 (131, datetime(2008, 3, 19, 8, 27, 29))],
                store = self._store
            )
        )
        self._runs[7].complete = True

        # course with 1 control, 3 rounds, time between punch 2 and 3 is < mindiff
        self._runs.append(
            Run(SICard(11),
                None,
                [(200, datetime(2008, 3, 19, 8, 22, 29)),
                 (201, datetime(2008, 3, 19, 8, 24, 29)),
                 (200, datetime(2008, 3, 19, 8, 24, 39)),
                 (200, datetime(2008, 3, 19, 8, 27, 29))],
                store = self._store
            )
        )
        self._runs[8].complete = True

        # course with 2 controls, 2 rounds, control 200 not punched one time
        self._runs.append(
            Run(SICard(12),
                None,
                [(131, datetime(2008, 3, 19, 8, 22, 29)),
                 (200, datetime(2008, 3, 19, 8, 23, 30)),
                 (131, datetime(2008, 3, 19, 8, 24, 29)),
                 (131, datetime(2008, 3, 19, 8, 23, 30)),
                 (131, datetime(2008, 3, 19, 8, 25, 29)),
                 (201, datetime(2008, 3, 19, 8, 26, 30)),
                 (131, datetime(2008, 3, 19, 8, 27, 29))],
                store = self._store
            ),
        )
        self._runs[9].complete = True

        self._finder = RunFinder(self._store)

    @staticmethod
    def _convert_punchlist(punchlist):
        return [(p[0], isinstance(p[1], Punch)
                 and p[1].sistation.id or p[1].code)
                for p in punchlist ]

    def _prepare_relay_team(testevent):
        """Prepares the team for relay testing."""
        # remove individual category
        for r in testevent._runners:
            r.category = None
        testevent._store.remove(testevent._cat_ind)

        testevent._runs[0].manual_start_time = None
        course_B = testevent._store.find(Course, Course.code == 'B').one()
        course_C = testevent._store.find(Course, Course.code == 'C').one()
        testevent._runs[1].course = course_B
        testevent._runs[2].course = course_C

    def _prepare_relay(testevent):
        testevent._prepare_relay_team()
        event = RelayEvent(
            {'D135': [{'name': '1',
                       'variants': ('A', ),
                       'starttime': testevent._team_start_time,
                       'defaulttime': None},
                      {'name': '2',
                       'variants': ('B', ),
                       'starttime': datetime(2008, 3, 19, 8, 40, 00),
                       'defaulttime': None},
                      {'name': '3',
                       'variants': ('C', ),
                       'starttime': datetime(2008, 3, 19, 8, 40, 00),
                       'defaulttime': None},
                      ],
            },
            store=testevent._store,
        )

        return event

    def _run_tuple(self, run_id):
        """
        @param run_id Index of the run in self._runs
        @return       Tuple formatted like RunFinder.get_results()"""

        r = self._runs[run_id]
        number = r.sicard.runner and r.sicard.runner.number or None
        team = r.sicard.runner and r.sicard.runner.team or None
        runner = r.sicard.runner
        return (r.id,
                r.course and str(r.course.code) or "unknown",
                "unknown",
                number and str(number) or "unknown",
                runner and str(runner) or "unknown",
                team and str(team) or "unknown",
                team and str(team.category) or runner and str(runner.category)
                  or "unkown")


class EventTest:

    def __init__(self, store):

        self._store = store

    def __enter__(self):

        # import runners from testfile
        importer = Team24hImporter(
            join(dirname(__file__), 'import_24h_team.csv'),
            'iso-8859-1',
        )
        importer.import_data(self._store)

        # import courses from testfile
        importer = OCADXMLCourseImporter(
            join(dirname(__file__), 'import_24h_course.xml'),
            finish = True,
            start = False,
        )
        importer.import_data(self._store)

        # import sample runs
        importer = SIRunImporter(join(dirname(__file__), 'import_24h_run.csv'))
        importer.import_data(self._store)

        self._cache = Cache()
        self._event = Relay24hEvent(
            starttime_24h = datetime(2008, 4, 14, 19, 0),
            starttime_12h = datetime(2008, 4, 15, 7, 0),
            speed = 5,
            header = {},
            duration_24h = timedelta(hours=4, minutes=30),
            duration_12h = timedelta(hours=4, minutes=30),
            cache = self._cache,
            store = self._store,
        )

        # commit to database
        self._store.commit()

        return self

    def __exit__(self, *args):

        # Clean up Database
        self._store.execute('TRUNCATE course CASCADE')
        self._store.execute('TRUNCATE sistation CASCADE')
        self._store.execute('TRUNCATE control CASCADE')
        self._store.execute('TRUNCATE run CASCADE')
        self._store.execute('TRUNCATE punch CASCADE')
        self._store.execute('TRUNCATE sicard CASCADE')
        self._store.execute('TRUNCATE runner CASCADE')
        self._store.execute('TRUNCATE category CASCADE')
        self._store.commit()

    def getTeam(self, number):
        return self._store.find(Team, Team.number == number).one()


@pytest.fixture
def store():
    store = Store(create_database('postgres:bosco_test'))
    yield store
    store.rollback()


@pytest.fixture
def testevent(store):
    return TestEvent(store)


@pytest.fixture
def eventtest(store):

    with EventTest(store) as eventtest:
        yield eventtest
