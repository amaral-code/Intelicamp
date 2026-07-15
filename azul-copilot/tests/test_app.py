import unittest
from app import app


class AppRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_endpoint(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        self.assertIn('ok', response.get_json()['status'])

    def test_homepage_contains_new_channel_copy(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('OmniBridge', response.get_data(as_text=True))

    def test_analyst_cannot_create_projects(self):
        response = self.client.post('/api/projects', json={
            'title': 'Nova ideia',
            'summary': 'Resumo de teste',
            'organization': 'Azul Conecta',
            'areas': ['TI'],
            'ownerRole': 'Analista',
            'userRole': 'Analista',
        })
        self.assertEqual(response.status_code, 403)
        self.assertIn('permissão', response.get_json()['error'].lower())

    def test_submitting_a_risky_project_triggers_marketing_alert_and_similarity(self):
        first = self.client.post('/api/projects', json={
            'title': 'Conexão Regional Premium',
            'summary': 'Projeto para fortalecer a conexão entre rotas regionais e o ecossistema Azul Viagens.',
            'organization': 'Azul Viagens',
            'areas': ['Marketing', 'Produtos'],
            'ownerRole': 'Gerente',
            'references': ['Campanha de conexão nacional']
        })
        self.assertEqual(first.status_code, 200)

        second = self.client.post('/api/projects', json={
            'title': 'Programa de corte de rotas',
            'summary': 'Vamos remover rotas locais e reduzir a conectividade para economizar custos.',
            'organization': 'Azul Conecta',
            'areas': ['TI', 'Operações'],
            'ownerRole': 'Analista',
            'references': ['Campanha de conexão nacional']
        })
        self.assertEqual(second.status_code, 200)
        payload = second.get_json()
        self.assertTrue(payload['marketingAlert']['needsMarketing'])
        self.assertTrue(payload['similarity']['hasSimilarProjects'])
        self.assertIn('marketing', payload['similarity']['notifications'])
        self.assertTrue(payload['project']['relatedProjects'])

    def test_comments_and_alerts_endpoints_are_available(self):
        response = self.client.get('/api/marketing-alerts')
        self.assertEqual(response.status_code, 200)
        self.assertIn('alerts', response.get_json())

        project_id = self.client.get('/api/projects').get_json()['projects'][0]['id']
        comment_response = self.client.post(f'/api/projects/{project_id}/comments', json={
            'author': 'Demo',
            'role': 'Analista',
            'text': 'Sugestão de revisão' 
        })
        self.assertEqual(comment_response.status_code, 200)
        self.assertEqual(comment_response.get_json()['project']['id'], project_id)


    def test_vote_on_project(self):
        project_id = self.client.get('/api/projects').get_json()['projects'][0]['id']
        response = self.client.post(f'/api/projects/{project_id}/vote', json={
            'vote': 'qualificado',
            'userId': 'test-user',
            'userName': 'Test User',
            'role': 'Diretor',
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('qualification', data)
        self.assertIn('qualificado', data['qualification'])
        self.assertGreaterEqual(data['qualification']['qualificado'], 1)

    def test_vote_invalid_payload(self):
        project_id = self.client.get('/api/projects').get_json()['projects'][0]['id']
        response = self.client.post(f'/api/projects/{project_id}/vote', json={'vote': 'invalido'})
        self.assertEqual(response.status_code, 400)

    def test_vote_requires_five_to_qualify(self):
        projects = self.client.get('/api/projects').get_json()['projects']
        self.client.post('/api/projects', json={
            'title': 'Projeto de teste',
            'summary': 'Resumo de teste para votação',
            'organization': 'Azul Conecta',
            'areas': ['TI'],
            'ownerRole': 'Gerente',
        })
        project_id = self.client.get('/api/projects').get_json()['projects'][0]['id']
        for i in range(7):
            self.client.post(f'/api/projects/{project_id}/vote', json={
                'vote': 'qualificado',
                'userId': f'user-{i}',
                'userName': f'User {i}',
                'role': 'Analista',
            })
        response = self.client.get(f'/api/projects/{project_id}/qualification')
        data = response.get_json()['qualification']
        self.assertEqual(data['status'], 'qualificado')
        self.assertGreaterEqual(data['qualificado'], 5)

    def test_director_vote_marker(self):
        project_id = self.client.get('/api/projects').get_json()['projects'][0]['id']
        self.client.post(f'/api/projects/{project_id}/vote', json={
            'vote': 'qualificado',
            'userId': 'dir-test',
            'userName': 'Dir Test',
            'role': 'Diretor',
        })
        qualification = self.client.get(f'/api/projects/{project_id}/qualification').get_json()['qualification']
        self.assertTrue(any(d['role'] == 'Diretor' for d in qualification['director_qualificado']))


if __name__ == '__main__':
    unittest.main()
