using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;

namespace backend.Models
{
    public class users
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int id { get; set; }
        public string login { get; set; }
        public string email { get; set; }
        public string password { get; set; }
        public bool is_admin { get; set; }

        // Списки
        public List<favorite_animals> favorite_animals { get; set; } = new();
        public List<test_score> test_score { get; set; } = new();
    }
}
